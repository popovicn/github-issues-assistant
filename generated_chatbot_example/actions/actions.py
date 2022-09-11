from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction, ValidationAction
from rasa_sdk.events import SlotSet, UserUtteranceReverted, BotUttered, FollowupAction, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from .github_client import GithubClient


FORM_FIELDS = {'issue_label': 'label', 'version': 'Which version of the product are you using?', 'answer_q0': 'When was the first time you experienced this issue?', 'answer_q1': 'Can you confirm this issue persist after deleting cache and cookies?', 'answer_q2': 'Would you like to be notified when this issue is resolved, and how?'}


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


class ValidatePredefinedSlots(ValidationAction):
    def validate_issue_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if isinstance(slot_value, str):
            # Strip optional # before issue number
            return {"issue_id": slot_value.strip("#")}
        else:
            return {"issue_id": None}


class ValidateSubmitIssueForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_submit_issue_form"

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
        gc = GithubClient()
        issues = gc.search_issue(slot_value)
        if issues:
            if len(issues) > 1:
                dispatcher.utter_message("Seems like similar issues exist:")
            else:
                dispatcher.utter_message("Seems like similar issue exists:")
            for issue in issues:
                dispatcher.utter_message(issue.short_description)
            return {
                "issue_description": slot_value,
                "FLAG_VALIDATE_ISSUE": True,
                "POSSIBLE_DUPLICATES": [i.to_json() for i in issues]
            }
        else:
            return {"issue_description": slot_value}


class UtterConfirmSubmitIssue(Action):

    def name(self) -> Text:
        return "ask_confirm_submit_issue"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("You provided following information:")
        dispatcher.utter_message('"{}"'.format(tracker.get_slot('issue_description')))
        for slot_name, question in FORM_FIELDS.items():
            slot_val = tracker.get_slot(slot_name)
            dispatcher.utter_message(text=f"  - {question}")
            dispatcher.utter_message(text=f'    "{slot_val}"')
        dispatcher.utter_message("Do you want to submit this issue?")
        return [SlotSet("FLAG_VALIDATE_FORM", True)]


class ActionSubmitIssueForm(Action):

    def name(self) -> Text:
        return "send_submit_issue_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        username = tracker.get_slot("gh_username")
        title = tracker.get_slot("issue_description")
        data = {}
        for slot_name, question in FORM_FIELDS.items():
            data[question] = tracker.get_slot(slot_name)
        possible_duplicates = tracker.get_slot("POSSIBLE_DUPLICATES")
        if possible_duplicates:
            data["possible_duplicates"] = possible_duplicates
        gc = GithubClient()
        issue_url = gc.create_issue(user=username, title=title, data=data)
        if issue_url:
            dispatcher.utter_message(
                f"Your issue has been submitted, you can track it at {issue_url}")
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
            "CONTINUE_SUBMIT_ISSUE",
            "POSSIBLE_DUPLICATES",
            "FLAG_VALIDATE_ISSUE",
            "FLAG_VALIDATE_FORM",
            "FLAG_CHECK_ISSUE_ACTIVE",
        ]
        reset_slots.extend(FORM_FIELDS)
        events = [SlotSet(slot, None) for slot in reset_slots]
        # Standard slots
        events.extend([
            ActiveLoop(None),
            SlotSet("requested_slot", None)
        ])
        return events


class ActionCheckIssueStatus(Action):
    def name(self) -> Text:
        return "action_check_issue"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        issue_id = tracker.get_slot("issue_id")
        gc = GithubClient()
        issue = gc.get_issue(issue_id)
        if issue:
            message = issue.description
        else:
            message = f"Issue #{issue_id} doesn't seem to exist."
        dispatcher.utter_message(message)
        return [SlotSet("issue_id", None)]
