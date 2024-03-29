import json
import re
import secrets
import string
from typing import Dict, List

from jinja2 import Template
from jsonpath_ng import parse

from ..providers.types import Content
from ..types import ActivityJob


def jsonpath(value: str, path: str) -> str:
    if not isinstance(value, str):
        value = json.dumps(value)
    expr = parse(path)
    for match in expr.find(json.loads(value)):
        return match.value
    return ""


class ActivityError(Exception):
    pass


class BaseActivity:
    MAX_ITERATIONS = 42

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, str]) -> None:
        pass

    @staticmethod
    def merge_inputs(inputs: Dict[str, str]) -> str:
        return "\n\n".join(inputs.values())

    @staticmethod
    def merge_inputs_json(inputs: Dict[str, str], indent=2) -> str:
        rval = {}
        for key, val in inputs.items():
            try:
                rval[key] = json.loads(val)
            except json.JSONDecodeError:
                rval[key] = val
        if len(rval.keys()) == 1:
            value = next(iter(rval.values()))
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            return json.dumps(value, indent=indent)
        else:
            return json.dumps(rval, indent=indent)

    @staticmethod
    def generate_temp_filename(prefix, extension, length=8):
        random_string = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
        return f"{prefix}_{random_string}.{extension}"

    @staticmethod
    def render(template: str, inputs: Dict[str, str]) -> str:
        inputs_json = {}
        for key, val in inputs.items():
            try:
                inputs_json[key] = json.loads(val)
            except json.JSONDecodeError:
                inputs_json[key] = val

        # Call a function to process path expressions
        str_template = template
        expr = r'{{([^.\[]+)([.\[])(.*)}}'
        for match in re.finditer(expr, template):
            activity_name = match.group(1)
            start_of_expression = match.group(2)
            path_expression = match.group(3)
            str_template = str_template.replace(match.group(0),
                                                '{{' +
                                                f'jsonpath({activity_name}, "$.{start_of_expression}{path_expression}")'
                                                + '}}',
                                                1)

        # Render the template
        jinja_template = Template(str_template)
        jinja_template.globals.update({
            "jsonpath": jsonpath
        })

        return jinja_template.render(inputs_json)

    @staticmethod
    def render_prompt(template: str, inputs: Dict[str, str]) -> str | List[Content]:
        text = BaseActivity.render(template, inputs)

        contents = []
        for key in inputs:
            if inputs[key].startswith("data:image"):
                contents.append(Content(type="image_url", image_url=inputs[key]))

        if len(contents) > 0:
            contents.insert(0, Content(type="text", text=text))
            return contents
        else:
            return text

