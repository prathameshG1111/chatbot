from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionProvideAdmissionDetails(Action):
    def name(self) -> Text:
        return "action_provide_admission_details"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        program = tracker.get_slot("program")
        branch = tracker.get_slot("branch")

        # Prompt if slots are missing
        if not program:
            dispatcher.utter_message(text="Please specify the program (UG, PG, or Diploma).")
            return []
        if not branch:
            dispatcher.utter_message(text="Please specify the branch.")
            return []

        intake_data = {
            "UG": {
                "Computer Engineering": 180,
                "Artificial Intelligence and Data Science": 180,
                "Electronics and Telecommunications": 180,
                "Mechanical Engineering": 180,
                "Electrical Engineering": 120,
                "Civil Engineering": 120,
            },
            "PG": {
                "VLSI & Embedded Systems": 24,
                "Computer Engineering": 36,
                "Mechanical Design Engineering": 24,
                "Structural Engineering": 24,
                "Construction Management": 24,
            },
            "Diploma": {
                "AI & ML": 120,
                "Computer Engineering": 120,
                "Mechanical Engineering": 60,
                "Civil Engineering": 60,
            },
        }

        # Convert branch name to a common format for lookup
        normalized_branch = branch.strip().title()

        intake = intake_data.get(program, {}).get(branch, None)

        if intake is None:
            dispatcher.utter_message(text=f"Sorry, {branch} is not a valid branch under {program}. Please choose a valid branch.")
            return []

        dispatcher.utter_message(
            text=(
                f"""
                    The admission process for {program} in {branch} is as follows:<br>
                    1. Fill out the <a href='https://docs.google.com/forms/d/e/1FAIpQLSealZj6ACWWcYv1KWwEtDWJ6SoirNnY1x3pTvQyaMSDYCVdMg/viewform' target='_blank'>Admission Enquiry Form</a>.<br>
                    2. Submit the required documents as mentioned in the <a href='https://adypsoe.in/docs/AdmissionBrochure/Information%20Brochure%202022-23.pdf' target='_blank'>Admission Brochure</a>.<br>
                    3. Appear for the entrance examination (if applicable).<br>
                    4. Review the <a href='https://adypsoe.in/fees.html' target='_blank'>Fee Structure</a>.<br>
                    5. Stay updated through the <a href='https://adypsoe.in/admission.html' target='_blank'>Admission Notifications</a>.<br><br>
                    Intake capacity: {intake} students.
                """
            )
        )
        return []

class ActionPredictCutoff(Action):
    def name(self):
        return "action_predict_cutoff"

    def run(self, dispatcher, tracker, domain):
        branch = tracker.get_slot("branch")
        university_type = tracker.get_slot("university_type")
        category = tracker.get_slot("category") or "Open"  # Default category

        if not branch:
            dispatcher.utter_message("Which branch are you asking the cutoff for?")
            return [SlotSet("branch", None)]

        if not university_type:
            dispatcher.utter_message("Is it for Home University (HU) or Other than Home University (OHU)?")
            return [SlotSet("university_type", None)]

        # Call the Flask API
        response = requests.post("http://localhost:5000/predict_cutoff", json={
            "branch": branch,
            "university_type": university_type,
            "category": category,
            "year": 2024
        })

        if response.status_code == 200:
            data = response.json()
            dispatcher.utter_message(f"The expected cutoff for {branch} ({university_type}, {category}) in {data['year']} is {data['predicted_cutoff']} percentile.")
        else:
            dispatcher.utter_message("Sorry, I couldn't fetch the cutoff details. Please try again.")

        return []