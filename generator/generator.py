import os
import shutil

import yaml


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.representer.SafeRepresenter.add_representer(str, str_presenter)    # noqa


class CustomSlot:

    def __init__(self, name, question, one_of):
        self.name = name
        self.question = question
        self.is_categorical = True if one_of else False
        self.one_of = one_of

    @property
    def slot_definition(self):
        mapping_type = "from_entity" if self.is_categorical else "from_text"

        slot_definition = {
            "type": "text",
            "mappings": [
                {
                    "type": mapping_type,
                    "not_intent": "cancel",
                    "conditions": [
                        {
                            "active_loop": "submit_issue_form",
                            "requested_slot": self.name
                        }
                    ]
                }
            ]
        }
        if self.is_categorical:
            slot_definition["mappings"][0]["entity"] = self.name
        return slot_definition

    @property
    def response(self):
        response = {
            "text": self.question
        }
        if self.is_categorical:
            response["buttons"] = []
            for answer in self.one_of:
                response["buttons"].append({
                    "title": answer,
                    "payload": f'/inform{{{{"{self.name}":"{answer}"}}}}'
                })
        return [response]


class ChatbotDir:
    def __init__(self, out_dir):
        self.dir = out_dir
        self.config = os.path.join(self.dir, 'config.yml')
        self.credentials = os.path.join(self.dir, 'credentials.yml')
        self.endpoints = os.path.join(self.dir, 'endpoints.yml')
        self.domain = os.path.join(self.dir, 'domain.yml')
        self.nlu = os.path.join(self.dir, 'data', 'nlu.yml')
        self.rules = os.path.join(self.dir, 'data', 'rules.yml')
        self.stories = os.path.join(self.dir, 'data', 'stories.yml')
        self.actions = os.path.join(self.dir, 'actions', 'actions.py')
        self.github_client = os.path.join(self.dir, 'actions', 'github_client.py')


class Generator:
    def __init__(self, name, out_dir, cfg):
        self.custom_slots = self._parse_custom_slots(cfg)
        self.name = name
        self.version = "3.1"
        self.out = ChatbotDir(out_dir)

    def _parse_custom_slots(self, cfg):
        custom_slots = []
        for question in cfg.get("questions", []):
            custom_slots.append(
                CustomSlot(
                    name=f"answer_q{len(custom_slots)}",
                    question=question.get("text"),
                    one_of=question.get("one_of")
                )
            )
        return custom_slots

    def _file_to_multiline_yaml(self, file_path) -> str:
        with open(file_path, 'r') as f:
            lines = []
            for line in f.readlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                lines.append(f"- {line}")
            return os.linesep.join(lines)

    def _generate_nlu(self):
        # Read intent templates
        files = dict()
        for (dir_path, _, file_names) in os.walk('templates/intents'):
            for file_name in file_names:
                intent_name = file_name.split(".")[0]
                files[intent_name] = os.path.join(dir_path, file_name)
        # Generate nlu.yml
        nlu = {
            "version": self.version,
            "nlu": []
        }
        for intent_name, file_path in files.items():
            nlu["nlu"].append({
                "intent": intent_name,
                "examples": self._file_to_multiline_yaml(file_path)
            })
        with open(self.out.nlu, 'w+') as nlu_file:
            yaml.safe_dump(nlu, nlu_file, sort_keys=False)

    def _configure_domain(self, domain):
        for slot in self.custom_slots:
            domain["entities"].append(slot.name)
            domain["slots"][slot.name] = slot.slot_definition
            response_name = f"utter_ask_submit_issue_form_{slot.name}"
            domain["responses"][response_name] = slot.response
            domain["forms"]["submit_issue_form"]["required_slots"].append(slot.name)
        return domain

    def _generate_domain(self):
        with open('templates/domain.yml', 'r') as f:
            domain = yaml.safe_load(f)
        domain = self._configure_domain(domain)
        with open(self.out.domain, 'w+') as f:
            yaml.safe_dump(domain, f, sort_keys=False)

    def _generate_actions(self):
        # Configure actions.py
        FORM_FIELDS = {
            'issue_label': 'label',
            'version': 'Which version of the product are you using?'
        }
        for slot in self.custom_slots:
            FORM_FIELDS[slot.name] = slot.question
        with open('templates/actions.py.txt', 'r') as f:
            actions_content = f.read()
            actions_content = actions_content.replace('<FORM_FIELDS>', str(FORM_FIELDS))
        with open(self.out.actions, 'w+') as f:
            f.write(actions_content)
        # Copy github_client.py
        shutil.copy('templates/github_client.py.txt', self.out.github_client)

    def _copy_static_files(self):
        shutil.copy('templates/rules.yml', self.out.rules)
        shutil.copy('templates/stories.yml', self.out.stories)
        shutil.copy('templates/config.yml', self.out.config)
        shutil.copy('templates/credentials.yml', self.out.credentials)
        shutil.copy('templates/endpoints.yml', self.out.endpoints)

    def init_chatbot(self):
        # Initialize chatbot directory
        if os.path.exists(self.out.dir):
            shutil.rmtree(self.out.dir)
        os.mkdir(self.out.dir)
        os.mkdir(os.path.join(self.out.dir, 'data'))
        actions_dir = os.path.join(self.out.dir, 'actions')
        os.mkdir(actions_dir)
        open(os.path.join(actions_dir, "__init__.py"), 'w+').close()

        # Write files
        self._generate_nlu()
        self._generate_domain()
        self._generate_actions()
        self._copy_static_files()


if __name__ == '__main__':
    chatbot_name = "generated_chatbot_example"
    out_dir = '../generated_chatbot_example'
    with open('example_config.yml', 'r') as f:
        cfg = yaml.safe_load(f)
    g = Generator(chatbot_name, out_dir, cfg)
    g.init_chatbot()
