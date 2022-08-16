# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import AllSlotsReset, SlotSet


class ActionReadUsername(Action):

    def name(self) -> Text:
        return "read_username"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        username = tracker.get_slot('username')
        dispatcher.utter_message(text=f"You are: {username}")
        return []


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
            "issue_label"
        ]
        dispatcher.utter_message("You provided following information:")
        for slot_name in take_slots:
            slot_val = tracker.get_slot(slot_name)
            dispatcher.utter_message(text=f"  {slot_name}: {slot_val}")
        dispatcher.utter_message("Do you want to submit this issue?")
        return []


class ActionSubmitIssueForm(Action):

    def name(self) -> Text:
        return "send_submit_issue_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        take_slots = [
            "issue_description",
            "issue_label"
        ]
        data = {}
        for slot_name in take_slots:
            data[slot_name] = tracker.get_slot(slot_name)

        dispatcher.utter_message(str(data))
        dispatcher.utter_message("Your issue has been submitted, you can track it on: <LINK>")

        return [
            SlotSet('issue_description', None),
            SlotSet('issue_label', None)
        ]
