from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet, UserUtteranceReverted, BotUttered, FollowupAction, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from .github_client import GithubClient


class ActionDefaultFallback(Action):
    """Executes the fallback action and goes back to the previous state
    of the dialogue"""

    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        active_form_name = tracker.active_loop.get("name")
        if active_form_name == "submit_issue_form":
            events = [
                UserUtteranceReverted(),    # Revert user message which led to fallback.
                BotUttered("Sorry, I didn't understand that."),
            ]
        else:
            events = [
                FollowupAction("action_listen")
            ]
        return events


class ValidateSubmitIssueForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_submit_issue_form"

    def _issue_exist(self, description):
        # TODO check github
        return True, "Existing issue description"

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Text]:
        additional_slots = []
        if tracker.slots.get("FLAG_VALIDATE_ISSUE") is True:
            additional_slots.append("CONTINUE_SUBMIT_ISSUE")
        return additional_slots + domain_slots

    def validate_issue_description(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        possible_duplicate, issues = self._issue_exist(slot_value)
        if possible_duplicate:
            dispatcher.utter_message("This issue already exits")
            return {
                "issue_description": slot_value,
                "FLAG_VALIDATE_ISSUE": True
            }
        else:
            return {"issue_description": slot_value}


class UtterConfirmSubmitIssue(Action):

    def name(self) -> Text:
        return "ask_confirm_submit_issue"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        take_slots = [
            "issue_description",
            "issue_label",
            "version"
        ]
        dispatcher.utter_message("You provided following information:")
        for slot_name in take_slots:
            slot_val = tracker.get_slot(slot_name)
            dispatcher.utter_message(text=f"  - {slot_name}: {slot_val}")
        dispatcher.utter_message("Do you want to submit this issue?")
        return [SlotSet("slot_validate_form", True)]


class ActionSubmitIssueForm(Action):

    def name(self) -> Text:
        return "send_submit_issue_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        username = tracker.get_slot("gh_username")
        title = tracker.get_slot("issue_description")
        take_slots = [
            # "gh_username",
            # "issue_description",
            "issue_label",
            "version"
        ]
        data = {}
        for slot_name in take_slots:
            data[slot_name] = tracker.get_slot(slot_name)

        gc = GithubClient()
        issue_url = gc.create_issue(user=username, title=title, **data)
        if issue_url:
            dispatcher.utter_message(
                f"Your issue has been submitted, you can track it here: {issue_url}")
        else:
            dispatcher.utter_message(
                "Sorry, your issue submission failed. Please contact support."
            )
        return []


class ActionResetAllSlotsExceptUsername(Action):

    def name(self) -> Text:
        return "reset_all_slots_except_username"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Slots from submit issue form
        reset_slots = [
            "issue_description",
            "issue_label",
            "version",
            "CONTINUE_SUBMIT_ISSUE",
            "FLAG_VALIDATE_ISSUE",
            "CONTINUE_SUBMIT_ISSUE"
        ]
        events = [SlotSet(slot, None) for slot in reset_slots]
        # Standard slots
        events.extend([
            SlotSet("slot_validate_form", False),
            SlotSet("FLAG_CHECK_ISSUE_ACTIVE", None),
            ActiveLoop(None),
            SlotSet("requested_slot", None)
        ])
        return events


class ActionCheckIssueStatus(Action):
    def name(self) -> Text:
        return "action_check_issue"

    def _get_issues(self):
        return {
            "123": "solved",
            "124": "open",
            "125": "declined"
        }

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        issue_id = tracker.get_slot("issue_id")
        issues_data = self._get_issues()
        if issue_id in issues_data:
            message = f"Issue #{issue_id} is {issues_data[issue_id]}"
        else:
            message = f"Issue #{issue_id} doesn't exist."
        dispatcher.utter_message(message)
        return [SlotSet("issue_id", None)]
