from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


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
        return []


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

        dispatcher.utter_message(str(data))
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
            "version"
        ]
        return [SlotSet(slot, None) for slot in reset_slots]
