import json
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, UserUtteranceReverted, BotUttered, FollowupAction, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher


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


class ActionChooseAction(Action):

    def name(self) -> Text:
        return "choose_action"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        opt = tracker.get_slot("ch_action")
        dispatcher.utter_message(text=f"You choose option: {opt}")
        return []


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
            dispatcher.utter_message(text=f">  {slot_name}: {slot_val}")
        dispatcher.utter_message("Do you want to submit this issue?")
        return [SlotSet("slot_validate_form", True)]


class ActionSubmitIssueForm(Action):

    def name(self) -> Text:
        return "send_submit_issue_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        take_slots = [
            "issue_description",
            "issue_label",
            "gh_username",
            "version"
        ]
        data = {}
        for slot_name in take_slots:
            data[slot_name] = tracker.get_slot(slot_name)

        dispatcher.utter_message("Your issue has been submitted, you can track it on: <LINK>")
        return []


class ActionResetAllSlotsExceptUsername(Action):

    def name(self) -> Text:
        return "reset_all_slots_except_username"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        reset_slots = [
            "issue_description",
            "issue_label",
            "version",
        ]
        events = [SlotSet(slot, None) for slot in reset_slots]
        events.extend([
            SlotSet("slot_validate_form", False),
            ActiveLoop(None),
            SlotSet("requested_slot", None)
        ])
        print(json.dumps(events, indent=4))
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
        dispatcher.utter_message(f"Issue {issue_id}")
        return []
