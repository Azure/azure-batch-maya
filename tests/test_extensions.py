# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import unittest
from mock import patch, Mock

from msrest import Serializer, Deserializer
from azure.storage import CloudStorageAccount
from azure.storage.blob.blockblobservice import BlockBlobService
import batch_extensions as batch
from batch_extensions.batch_auth import SharedKeyCredentials
from batch_extensions import models
from batch_extensions import operations
from batch_extensions import _template_utils as utils
from batch_extensions import _pool_utils as pool_utils
from batch_extensions import _file_utils as file_utils



class TestBatchExtensions(unittest.TestCase):
    # pylint: disable=attribute-defined-outside-init,no-member,too-many-public-methods

    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'json_data')
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

        # File path to an application template with no parameters - a static
        # template that always does exactly the same thing
        self.static_apptemplate_path = os.path.join(self.data_dir,
            'batch-applicationTemplate-static.json')

        # File path to an application path with parameters
        self.apptemplate_with_params_path = os.path.join(self.data_dir,
            'batch-applicationTemplate-parameters.json')
        return super(TestBatchExtensions, self).setUp()

    def test_batch_extensions_expression_evaluation(self):
        # It should replace a string containing only an expression
        definition = {'value': "['evaluateMe']"}
        template = json.dumps(definition)
        parameters = {}
        result = utils._parse_template(template, definition, parameters)  # pylint:disable=protected-access
        self.assertEqual(result['value'], 'evaluateMe')

        # It should replace an expression within a string
        definition = {'value': "prequel ['alpha'] sequel"}
        template = json.dumps(definition)
        parameters = {}
        result = utils._parse_template(template, definition, parameters)  # pylint:disable=protected-access
        self.assertEqual(result['value'], 'prequel alpha sequel')

        # It should replace multiple expressions within a string
        definition = {'value': "prequel ['alpha'] interquel ['beta'] sequel"}
        template = json.dumps(definition)
        parameters = {}
        result = utils._parse_template(template, definition, parameters)  # pylint:disable=protected-access
        self.assertEqual(result['value'], 'prequel alpha interquel beta sequel')

        # It should unescape an escaped expression
        definition = {'value': "prequel [['alpha'] sequel"}
        template = json.dumps(definition)
        parameters = {}
        result = utils._parse_template(template, definition, parameters)  # pylint:disable=protected-access
        self.assertEqual(result['value'], "prequel ['alpha'] sequel")

        # It should not choke on JSON containing string arrays
        definition = {'values': ["alpha", "beta", "gamma", "[43]"]}
        template = json.dumps(definition)
        parameters = {}
        result = utils._parse_template(template, definition, parameters)  # pylint:disable=protected-access
        self.assertEqual(result['values'], ["alpha", "beta", "gamma", "43"])

        # It should not choke on JSON containing number arrays
        definition = {'values': [1, 1, 2, 3, 5, 8, 13]}
        template = json.dumps(definition)
        parameters = {}
        result = utils._parse_template(template, definition, parameters)  # pylint:disable=protected-access
        self.assertEqual(result['values'], [1, 1, 2, 3, 5, 8, 13])

    def test_batch_extensions_parameters(self):

        # It should replace string value for a string parameter
        template = {
            'result': "[parameters('code')]",
            'parameters': {
                'code': {'type': 'string'}
            }
        }
        temaplate_string = json.dumps(template)
        parameters = {'code': 'stringValue'}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "stringValue")

        # It should replace numeric value for string parameter as a string
        parameters = {'code': 42}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "42")

        # It should replace int value for int parameter
        template = {
            'result': "[parameters('code')]",
            'parameters': {
                'code': {'type': 'int'}
            }
        }
        temaplate_string = json.dumps(template)
        parameters = {'code': 42}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], 42)

        # It should replace string value for int parameter as int
        parameters = {'code': "42"}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], 42)

        # It should replace int values for int parameters in nested expressions
        template = {
            'framesize': "Framesize is ([parameters('width')]x[parameters('height')])",
            'parameters': {
                'width': {'type': 'int'},
                'height': {'type': 'int'}
            }
        }
        temaplate_string = json.dumps(template)
        parameters = {'width': 1920, 'height': 1080}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['framesize'], "Framesize is (1920x1080)")

        # It should replace bool value for bool parameter
        template = {
            'result': "[parameters('code')]",
            'parameters': {
                'code': {'type': 'bool'}
            }
        }
        temaplate_string = json.dumps(template)
        parameters = {'code': True}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], True)

        # It should replace string value for bool parameter as bool value
        parameters = {'code': 'true'}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], True)

        # It should report an error for an unsupported parameter type
        template = {
            'result': "[parameters('code')]",
            'parameters': {
                'code': {'type': 'currency'}
            }
        }
        temaplate_string = json.dumps(template)
        parameters = {'code': True}
        with self.assertRaises(TypeError):
            utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access

    def test_batch_extensions_variables(self):

        # It should replace value for a variable
        template = {
            'result': "[variables('code')]",
            "variables": {
                "code": "enigmatic"
            }
        }
        temaplate_string = json.dumps(template)
        parameters = {}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "enigmatic")

        # It should replace function result for a variable
        template = {
            'result': "[variables('code')]",
            "variables": {
                "code": "[concat('this', '&', 'that')]"
            }
        }
        temaplate_string = json.dumps(template)
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "this&that")

    def test_batch_extensions_concat(self):

        # It should handle strings
        template = {
            "result": "[concat('alpha', 'beta', 'gamma')]"
        }
        temaplate_string = json.dumps(template)
        parameters = {}
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "alphabetagamma")

        # It should handle strings and numbers
        template = {
            "result": "[concat('alpha', 42, 'beta', 3, '.', 1415, 'gamma')]"
        }
        temaplate_string = json.dumps(template)
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "alpha42beta3.1415gamma")

        # It should handle strings containing commas correctly
        template = {
            "result": "[concat('alpha', ', ', 'beta', ', ', 'gamma')]"
        }
        temaplate_string = json.dumps(template)
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "alpha, beta, gamma")

        # It should handle strings containing square brackets correctly
        template = {
            "result": "[concat('alpha', '[', 'beta', ']', 'gamma')]"
        }
        temaplate_string = json.dumps(template)
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "alpha[beta]gamma")

        # It should handle nested concat function calls
        template = {
            "result": "[concat('alpha ', concat('this', '&', 'that'), ' gamma')]"
        }
        temaplate_string = json.dumps(template)
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "alpha this&that gamma")

        # It should handle nested parameters() function calls
        template = {
            "result": "[concat('alpha ', parameters('name'), ' gamma')]",
            "parameters": {
                "name": {"type": "string"}
            }
        }
        parameters = {"name": "Frodo"}
        temaplate_string = json.dumps(template)
        resolved = utils._parse_template(temaplate_string, template, parameters)  # pylint:disable=protected-access
        self.assertEqual(resolved['result'], "alpha Frodo gamma")

    def test_batch_extensions_expand_template_with_parameter_file(self):
        template_file = os.path.join(self.data_dir, 'batch.job.parametricsweep.json')
        parameter_file = os.path.join(self.data_dir, 'batch.job.parameters.json')
        job_ops = operations.ExtendedJobOperations(None, None, None, self._serialize, self._deserialize, None)
        resolved = job_ops.expand_template(template_file, parameter_file)
        self.assertTrue(resolved)
        self.assertEqual(resolved['id'], "helloworld")
        self.assertEqual(resolved['poolInfo']['poolId'], "xplatTestPool")
        self.assertFalse('[parameters(' in json.dumps(resolved))

    def test_batch_extensions_replace_parametric_sweep_command(self):
        test_input = Mock(value="cmd {{{0}}}.mp3 {1}.mp3")
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 10])
        self.assertEqual(test_input.value, 'cmd {5}.mp3 10.mp3')
        test_input.value = "cmd {{{0}}}.mp3 {{{1}}}.mp3"
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 10])
        self.assertEqual(test_input.value, 'cmd {5}.mp3 {10}.mp3')
        test_input.value = "cmd {{0}}.mp3 {1}.mp3"
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 10])
        self.assertEqual(test_input.value, 'cmd {0}.mp3 10.mp3')
        test_input.value = "cmd {0}.mp3 {1}.mp3"
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 10])
        self.assertEqual(test_input.value, 'cmd 5.mp3 10.mp3')
        test_input.value = "cmd {0}{1}.mp3 {1}.mp3"
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 10])
        self.assertEqual(test_input.value, 'cmd 510.mp3 10.mp3')
        test_input.value = "cmd {0}.mp3 {0}.mp3"
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 10])
        self.assertEqual(test_input.value, 'cmd 5.mp3 5.mp3')
        test_input.value = "cmd {0:3}.mp3 {0}.mp3"
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 10])
        self.assertEqual(test_input.value, 'cmd 005.mp3 5.mp3')
        test_input.value = "cmd {0:3}.mp3 {1:3}.mp3"
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 1234])
        self.assertEqual(test_input.value, 'cmd 005.mp3 1234.mp3')
        test_input.value = "cmd {{}}.mp3"
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5, 1234])
        self.assertEqual(test_input.value, 'cmd {}.mp3')
        test_input.value = ("gs -dQUIET -dSAFER -dBATCH -dNOPAUSE -dNOPROMPT -sDEVICE=pngalpha "
                               "-sOutputFile={0}-%03d.png -r250 {0}.pdf && for f in *.png;"
                               " do tesseract $f ${{f%.*}};done")
        utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                     test_input, "value", [5])
        self.assertEqual(
            test_input.value,
            "gs -dQUIET -dSAFER -dBATCH -dNOPAUSE -dNOPROMPT -sDEVICE=pngalpha "
            "-sOutputFile=5-%03d.png -r250 5.pdf && for f in *.png; do tesseract "
            "$f ${f%.*};done")

    def test_batch_extensions_replace_invalid_parametric_sweep(self):

        test_input = Mock(value="cmd {0}.mp3 {2}.mp3")
        with self.assertRaises(ValueError):
            utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                         test_input, "value", [5, 10])
        test_input.value = "cmd {}.mp3 {2}.mp3"
        with self.assertRaises(ValueError):
            utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                         test_input, "value", [5, 10])
        test_input.value = "cmd {{0}}}.mp3 {1}.mp3"
        with self.assertRaises(ValueError):
            utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                         test_input, "value", [5, 10])
        test_input.value = "cmd {0:3}.mp3 {1}.mp3"
        with self.assertRaises(ValueError):
            utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                         test_input, "value", [-5, 10])
        test_input.value = "cmd {0:-3}.mp3 {1}.mp3"
        with self.assertRaises(ValueError):
            utils._replacement_transform(utils._transform_sweep_str,  # pylint:disable=protected-access
                                         test_input, "value", [5, 10])

    def test_batch_extensions_replace_file_iteration_command(self):
        file_info = {
            "url": "http://someurl/container/path/blob.ext",
            "filePath": "path/blob.ext",
            "fileName": "blob.ext",
            "fileNameWithoutExtension": "blob"
        }
        test_input = Mock(value="cmd {{{url}}}.mp3 {filePath}.mp3")
        utils._replacement_transform(utils._transform_file_str,  # pylint:disable=protected-access
                                     test_input, "value", file_info)
        self.assertEqual(test_input.value,
                         'cmd {http://someurl/container/path/blob.ext}.mp3 path/blob.ext.mp3')
        test_input.value = "cmd {{{fileName}}}.mp3 {{{fileNameWithoutExtension}}}.mp3"
        utils._replacement_transform(utils._transform_file_str,  # pylint:disable=protected-access
                                     test_input, "value", file_info)
        self.assertEqual(test_input.value, 'cmd {blob.ext}.mp3 {blob}.mp3')
        test_input.value = "cmd {{fileName}}.mp3 {fileName}.mp3"
        utils._replacement_transform(utils._transform_file_str,  # pylint:disable=protected-access
                                    test_input, "value", file_info)
        self.assertEqual(test_input.value, 'cmd {fileName}.mp3 blob.ext.mp3')
        test_input.value = (
            "gs -dQUIET -dSAFER -dBATCH -dNOPAUSE -dNOPROMPT -sDEVICE=pngalpha "
            "-sOutputFile={fileNameWithoutExtension}-%03d.png -r250 "
            "{fileNameWithoutExtension}.pdf && for f in *.png; do tesseract $f ${{f%.*}};done")
        utils._replacement_transform(utils._transform_file_str,  # pylint:disable=protected-access
                                     test_input, "value", file_info)
        self.assertEqual(
            test_input.value,
            "gs -dQUIET -dSAFER -dBATCH -dNOPAUSE -dNOPROMPT -sDEVICE=pngalpha "
            "-sOutputFile=blob-%03d.png -r250 blob.pdf && for f in *.png; do tesseract "
            "$f ${f%.*};done")

    def test_batch_extensions_replace_invalid_file_iteration_command(self):
        file_info = {
            "url": "http://someurl/container/path/blob.ext",
            "filePath": "path/blob.ext",
            "fileName": "blob.ext",
            "fileNameWithoutExtension": "blob"
        }
        test_input = Mock(value="cmd {url}.mp3 {fullNameWithSome}.mp3")
        with self.assertRaises(ValueError):
            utils._replacement_transform(utils._transform_file_str,  # pylint:disable=protected-access
                                         test_input, "value", file_info)
        test_input.value = "cmd {}.mp3 {url}.mp3"
        with self.assertRaises(ValueError):
            utils._replacement_transform(utils._transform_file_str,  # pylint:disable=protected-access
                                         test_input, "value", file_info)
        test_input.value = "cmd {{url}}}.mp3 {filePath}.mp3"
        with self.assertRaises(ValueError):
            utils._replacement_transform(utils._transform_file_str,  # pylint:disable=protected-access
                                         test_input, "value", file_info)

    def test_batch_extensions_parse_parameter_sets(self):
        parsed = utils._parse_parameter_sets([models.ParameterSet(start=1, end=2)])  # pylint:disable=protected-access
        self.assertEqual(list(parsed), [(1,), (2,)])
        parsed = utils._parse_parameter_sets([models.ParameterSet(start=1, end=1)])  # pylint:disable=protected-access
        self.assertEqual(list(parsed), [(1,)])
        parsed = utils._parse_parameter_sets([  # pylint:disable=protected-access
            models.ParameterSet(start=1, end=2),
            models.ParameterSet(start=-1, end=-3, step=-1)])
        self.assertEqual(list(parsed), [(1, -1), (1, -2), (1, -3), (2, -1), (2, -2), (2, -3)])
        parsed = utils._parse_parameter_sets([  # pylint:disable=protected-access
            models.ParameterSet(start=1, end=2),
            models.ParameterSet(start=-1, end=-3, step=-1),
            models.ParameterSet(start=-5, end=5, step=3)])
        self.assertEqual(list(parsed), [(1, -1, -5), (1, -1, -2), (1, -1, 1), (1, -1, 4),
                                        (1, -2, -5), (1, -2, -2), (1, -2, 1), (1, -2, 4),
                                        (1, -3, -5), (1, -3, -2), (1, -3, 1), (1, -3, 4),
                                        (2, -1, -5), (2, -1, -2), (2, -1, 1), (2, -1, 4),
                                        (2, -2, -5), (2, -2, -2), (2, -2, 1), (2, -2, 4),
                                        (2, -3, -5), (2, -3, -2), (2, -3, 1), (2, -3, 4)])
        parsed = utils._parse_parameter_sets([  # pylint:disable=protected-access
            models.ParameterSet(start=1, end=2, step=2000),
            models.ParameterSet(start=-1, end=-3, step=-1),
            models.ParameterSet(start=-5, end=5, step=3)])
        self.assertEqual(list(parsed), [(1, -1, -5), (1, -1, -2), (1, -1, 1), (1, -1, 4),
                                        (1, -2, -5), (1, -2, -2), (1, -2, 1), (1, -2, 4),
                                        (1, -3, -5), (1, -3, -2), (1, -3, 1), (1, -3, 4)])
        parsed = list(utils._parse_parameter_sets([models.ParameterSet(start=1, end=2000)]))  # pylint:disable=protected-access,redefined-variable-type
        self.assertEqual(len(parsed), 2000)
        self.assertEqual(len(parsed[0]), 1)

    def test_batch_extensions_parse_invalid_parameter_set(self):
        with self.assertRaises(ValueError):
            utils._parse_parameter_sets([])  # pylint:disable=protected-access
        with self.assertRaises(ValueError):
            utils._parse_parameter_sets([Mock(start=2, end=1, step=1)])  # pylint:disable=protected-access
        with self.assertRaises(ValueError):
            models.ParameterSet(start=2, end=1)
        with self.assertRaises(ValueError):
            utils._parse_parameter_sets([Mock(start=1, end=3, step=-1)])  # pylint:disable=protected-access
        with self.assertRaises(ValueError):
            models.ParameterSet(start=1, end=3, step=-1)
        with self.assertRaises(ValueError):
            utils._parse_parameter_sets([Mock(start=1, end=3, step=0)])  # pylint:disable=protected-access
        with self.assertRaises(ValueError):
            models.ParameterSet(start=1, end=3, step=0)
        with self.assertRaises(ValueError):
            utils._parse_parameter_sets([Mock(start=None, end=3, step=1)])  # pylint:disable=protected-access
        with self.assertRaises(ValueError):
            models.ParameterSet(start=None, end=3, step=1)
        with self.assertRaises(ValueError):
            utils._parse_parameter_sets([Mock(start=3, end=None, step=1)])  # pylint:disable=protected-access
        with self.assertRaises(ValueError):
            models.ParameterSet(start=3, end=None, step=1)
        with self.assertRaises(ValueError):
            utils._parse_parameter_sets([Mock(start=1, end=2, step=1), Mock(start=None, end=None, step=1)])  # pylint:disable=protected-access
        with self.assertRaises(ValueError):
            models.ParameterSet(start=None, end=None)

    def test_batchextensions_parse_taskcollection_factory(self):
        template = models.TaskCollectionTaskFactory(
            tasks=[
                models.ExtendedTaskParameter(
                    id="mytask1",
                    command_line="ffmpeg -i sampleVideo1.mkv"
                                 " -vcodec copy -acodec copy output.mp4 -y",
                    resource_files=[
                        models.ExtendedResourceFile(
                            blob_source="[parameters('inputFileStorageContainerUrl')]"
                                        "sampleVideo1.mkv",
                            file_path="sampleVideo1.mkv")
                    ],
                    output_files=[
                        models.OutputFile(
                            file_pattern="output.mp4",
                            destination=models.ExtendedOutputFileDestination(
                                container=models.OutputFileBlobContainerDestination(
                                    container_url="[parameters('outputFileStorageUrl')]")),
                            upload_options=models.OutputFileUploadOptions(
                                upload_condition=models.OutputFileUploadCondition.task_completion))
                    ])
            ])
        result = utils._expand_task_collection(template)  # pylint: disable=protected-access
        self.assertEqual(result, template.tasks)        

    def test_batch_extensions_parse_parametricsweep_factory(self):
        template = models.ParametricSweepTaskFactory(
            parameter_sets=[
                models.ParameterSet(1, 2),
                models.ParameterSet(3, 5)
            ],
            repeat_task= models.RepeatTask("cmd {0}.mp3 {1}.mp3"))
        result = utils._expand_parametric_sweep(template)  # pylint:disable=protected-access
        expected = [
            models.ExtendedTaskParameter('0', 'cmd 1.mp3 3.mp3'),
            models.ExtendedTaskParameter('1', 'cmd 1.mp3 4.mp3'),
            models.ExtendedTaskParameter('2', 'cmd 1.mp3 5.mp3'),
            models.ExtendedTaskParameter('3', 'cmd 2.mp3 3.mp3'),
            models.ExtendedTaskParameter('4', 'cmd 2.mp3 4.mp3'),
            models.ExtendedTaskParameter('5', 'cmd 2.mp3 5.mp3')
        ]
        for index, task in enumerate(result):
            self.assertEqual(expected[index].id, task.id)
            self.assertEqual(expected[index].command_line, task.command_line)

        template = models.ParametricSweepTaskFactory(
            parameter_sets=[models.ParameterSet(1, 3)],
            repeat_task= models.RepeatTask("cmd {0}.mp3",
                resource_files=[
                    models.ResourceFile("http://account.blob/run.exe", "run.exe"),
                    models.ResourceFile("http://account.blob/{0}.dat", "{0}.mp3")],
                output_files=[models.OutputFile(
                    file_pattern="{0}.txt",
                    destination=models.ExtendedOutputFileDestination(
                        container=models.OutputFileBlobContainerDestination(
                            path="{0}",
                            container_url="{0}sas"
                        )
                    ),
                    upload_options=models.OutputFileUploadOptions(
                        upload_condition=models.OutputFileUploadCondition.task_success
                    )
                )]))
        expected = [
            models.ExtendedTaskParameter('0', 'cmd 1.mp3',
                resource_files=[
                    models.ResourceFile("http://account.blob/run.exe", "run.exe"),
                    models.ResourceFile("http://account.blob/1.dat", "1.mp3")],
                output_files=[models.OutputFile(
                    file_pattern="1.txt",
                    destination=models.ExtendedOutputFileDestination(
                        container=models.OutputFileBlobContainerDestination(
                            path="1",
                            container_url="1sas"
                        )
                    ),
                    upload_options=models.OutputFileUploadOptions(
                        upload_condition=models.OutputFileUploadCondition.task_success
                    ))]),
            models.ExtendedTaskParameter('1', 'cmd 2.mp3',
                resource_files=[
                    models.ResourceFile("http://account.blob/run.exe", "run.exe"),
                    models.ResourceFile("http://account.blob/2.dat", "2.mp3")],
                output_files=[models.OutputFile(
                    file_pattern="2.txt",
                    destination=models.ExtendedOutputFileDestination(
                        container=models.OutputFileBlobContainerDestination(
                            path="2",
                            container_url="2sas"
                        )
                    ),
                    upload_options=models.OutputFileUploadOptions(
                        upload_condition=models.OutputFileUploadCondition.task_success
                    ))]),
            models.ExtendedTaskParameter('2', 'cmd 3.mp3',
                resource_files=[
                    models.ResourceFile("http://account.blob/run.exe", "run.exe"),
                    models.ResourceFile("http://account.blob/3.dat", "3.mp3")],
                output_files=[models.OutputFile(
                    file_pattern="3.txt",
                    destination=models.ExtendedOutputFileDestination(
                        container=models.OutputFileBlobContainerDestination(
                            path="3",
                            container_url="3sas"
                        )
                    ),
                    upload_options=models.OutputFileUploadOptions(
                        upload_condition=models.OutputFileUploadCondition.task_success
                    ))]),
        ]
        result = utils._expand_parametric_sweep(template)  # pylint: disable=protected-access
        for index, task in enumerate(result):
            self.assertEqual(expected[index].command_line, task.command_line)
            self.assertEqual(expected[index].resource_files[1].blob_source, task.resource_files[1].blob_source)
            self.assertEqual(expected[index].resource_files[1].file_path, task.resource_files[1].file_path)
            self.assertEqual(expected[index].output_files[0].file_pattern, task.output_files[0].file_pattern)
        
        template = models.ParametricSweepTaskFactory(
            parameter_sets=[
                models.ParameterSet(1, 3)
            ],
            repeat_task= models.RepeatTask("cmd {0}.mp3"),
            merge_task=models.MergeTask("summary.exe"))
        expected = [
            models.ExtendedTaskParameter('0', 'cmd 1.mp3'),
            models.ExtendedTaskParameter('1', 'cmd 2.mp3'),
            models.ExtendedTaskParameter('2', 'cmd 3.mp3'),
            models.ExtendedTaskParameter('merge', 'summary.exe',
                depends_on=models.TaskDependencies(task_id_ranges=models.TaskIdRange(0, 2)))
        ]
        result = utils._expand_parametric_sweep(template)  # pylint: disable=protected-access
        for index, task in enumerate(result):
            self.assertEqual(expected[index].command_line, task.command_line)
        self.assertEqual(result[-1].id, 'merge')
        self.assertEqual(result[-1].depends_on.task_id_ranges.start, 0)
        self.assertEqual(result[-1].depends_on.task_id_ranges.end, 2)

    def test_batch_extensions_parse_invalid_parametricsweep(self):

        with self.assertRaises(ValueError):
            utils._expand_parametric_sweep(Mock(parameter_sets=None, repeat_task=models.RepeatTask('cmd {0}.mp3')))  # pylint: disable=protected-access
        with self.assertRaises(ValueError):
            utils._expand_parametric_sweep(Mock(parameter_sets=[models.ParameterSet(1, 3)], repeat_task=None))  # pylint: disable=protected-access
        template = models.ParametricSweepTaskFactory(
            parameter_sets=[
                models.ParameterSet(1, 3)
            ],
            repeat_task=models.RepeatTask(
                command_line=None,
                resource_files=[
                    models.ResourceFile(
                        file_path="run.exe",
                        blob_source="http://account.blob/run.exe"),
                    models.ResourceFile(
                        file_path="{0}.mp3",
                        blob_source="http://account.blob/{0}.dat")
                ]
            )
        )
        with self.assertRaises(ValueError):
            utils._expand_parametric_sweep(template)  # pylint: disable=protected-access
        template = models.ParametricSweepTaskFactory(
            parameter_sets=[
                models.ParameterSet(1, 3)
            ],
            repeat_task=models.RepeatTask(
                command_line="cmd {0}.mp3",
                resource_files=[
                    models.ResourceFile(
                        file_path="run.exe",
                        blob_source="http://account.blob/run.exe"),
                    models.ResourceFile(
                        file_path="{0}.mp3",
                        blob_source="http://account.blob/{0}.dat")
                ]
            )
        )
        utils._expand_parametric_sweep(template)  # pylint: disable=protected-access

    def test_batch_extensions_preserve_resourcefiles(self):
        fileutils = file_utils.FileUtils(None)
        request = Mock(
            resource_files=[
                Mock(
                    blob_source='abc',
                    file_path='xyz')
            ])
        transformed = utils.post_processing(request, fileutils, pool_utils.PoolOperatingSystemFlavor.LINUX)
        self.assertEqual(transformed, request)
        request = Mock(
            common_resource_files=[
                Mock(
                    blob_source='abc',
                    file_path='xyz')
            ],
            job_manager_task=Mock(
                resource_files=[
                    Mock(
                        blob_source='foo',
                        file_path='bar')
                ]
            )
        )
        transformed = utils.post_processing(request, fileutils, pool_utils.PoolOperatingSystemFlavor.WINDOWS)
        self.assertEqual(transformed, request)
        request = [  # pylint: disable=redefined-variable-type
            Mock(resource_files=[Mock(blob_source='abc', file_path='xyz')]),
            Mock(resource_files=[Mock(blob_source='abc', file_path='xyz')])
        ]
        transformed = utils.post_processing(request, fileutils, pool_utils.PoolOperatingSystemFlavor.WINDOWS)
        self.assertEqual(transformed, request)
        request = Mock(resource_files=[Mock(blob_source='abc', file_path=None)])
        with self.assertRaises(ValueError):
            utils.post_processing(request, fileutils, pool_utils.PoolOperatingSystemFlavor.WINDOWS)

    def test_batch_extensions_validate_parameter(self):
        content = {
            'a': {
                "type": "int",
                "maxValue": 5,
                "minValue": 3
            },
            'b': {
                "type": "string",
                "maxLength": 5,
                "minLength": 3
            },
            'c': {
                "type": "string",
                "allowedValues": [
                    "STANDARD_A1",
                    "STANDARD_A2",
                    "STANDARD_A3",
                    "STANDARD_A4",
                    "STANDARD_D1",
                    "STANDARD_D2",
                    "STANDARD_D3",
                    "STANDARD_D4"
                ]
            },
            'd': {
                "type": "bool"
            }
        }
        # pylint: disable=protected-access
        self.assertEqual(utils._validate_parameter('a', content['a'], 3), 3)
        self.assertEqual(utils._validate_parameter('a', content['a'], 5), 5)
        with self.assertRaises(ValueError):
            utils._validate_parameter('a', content['a'], 1)
        with self.assertRaises(ValueError):
            utils._validate_parameter('a', content['a'], 10)
        with self.assertRaises(TypeError):
            utils._validate_parameter('a', content['a'], 3.1)
        self.assertEqual(utils._validate_parameter('b', content['b'], 'abcd'), 'abcd')
        with self.assertRaises(ValueError):
            utils._validate_parameter('b', content['b'], 'a')
        with self.assertRaises(ValueError):
            utils._validate_parameter('b', content['b'], 'abcdeffg')
        with self.assertRaises(ValueError):
            utils._validate_parameter('b', content['b'], 1)
        self.assertEqual(utils._validate_parameter('b', content['b'], 100), '100')
        self.assertEqual(utils._validate_parameter('c', content['c'],
                                                   'STANDARD_A1'), 'STANDARD_A1')
        with self.assertRaises(ValueError):
            utils._validate_parameter('c', content['c'], 'STANDARD_C1')
        with self.assertRaises(ValueError):
            utils._validate_parameter('c', content['c'], 'standard_a1')
        self.assertEqual(utils._validate_parameter('d', content['d'], True), True)
        self.assertEqual(utils._validate_parameter('d', content['d'], False), False)
        self.assertEqual(utils._validate_parameter('d', content['d'], 'true'), True)
        self.assertEqual(utils._validate_parameter('d', content['d'], 'false'), False)
        with self.assertRaises(TypeError):
            utils._validate_parameter('d', content['d'], 'true1')
        with self.assertRaises(TypeError):
            utils._validate_parameter('d', content['d'], 3)

    def test_batch_extensions_simple_linux_package_manager(self):
        pool = models.ExtendedPoolParameter(
            id="testpool",
            virtual_machine_configuration=models.VirtualMachineConfiguration(
                image_reference=models.ImageReference(
                    publisher="Canonical",
                    offer="UbuntuServer",
                    sku="15.10",
                    version="latest"
                ),
                node_agent_sku_id="batch.node.debian 8"
            ),
            vm_size="STANDARD_A1",
            target_dedicated_nodes="10",
            enable_auto_scale=False,
            package_references=[
                models.AptPackageReference("ffmpeg"),
                models.AptPackageReference("apache2", "12.34")
            ]
        )
        commands = [utils.process_pool_package_references(pool)]
        pool.start_task = models.StartTask(**utils.construct_setup_task(
            pool.start_task, commands,
            pool_utils.PoolOperatingSystemFlavor.LINUX))
        self.assertEqual(pool.start_task.command_line,
                         "/bin/bash -c 'apt-get update;apt-get install -y "
                         "ffmpeg;apt-get install -y apache2=12.34'")
        self.assertEqual(pool.start_task.user_identity.auto_user.elevation_level, 'admin')
        self.assertTrue(pool.start_task.wait_for_success)

    def test_batch_extensions_simple_windows_package_manager(self):
        pool = models.ExtendedPoolParameter(
            id="testpool",
            virtual_machine_configuration=models.VirtualMachineConfiguration(
                image_reference=models.ImageReference(
                    publisher="MicrosoftWindowsServer",
                    offer="WindowsServer",
                    sku="2012-Datacenter",
                    version="latest"
                ),
                node_agent_sku_id="batch.node.windows amd64"
            ),
            vm_size="STANDARD_A1",
            target_dedicated_nodes="10",
            enable_auto_scale=False,
            package_references=[
                models.ChocolateyPackageReference("ffmpeg"),
                models.ChocolateyPackageReference("testpkg", "12.34", True)
            ]
        )
        commands = [utils.process_pool_package_references(pool)]
        pool.start_task = models.StartTask(**utils.construct_setup_task(
            pool.start_task, commands,
            pool_utils.PoolOperatingSystemFlavor.WINDOWS))
        self.assertEqual(
            pool.start_task.command_line,
            'cmd.exe /c "powershell -NoProfile -ExecutionPolicy unrestricted '
            '-Command "(iex ((new-object net.webclient).DownloadString('
            '\'https://chocolatey.org/install.ps1\')))" && SET PATH="%PATH%;'
            '%ALLUSERSPROFILE%\\chocolatey\\bin" && choco feature enable '
            '-n=allowGlobalConfirmation & choco install ffmpeg & choco install testpkg '
            '--version 12.34 --allow-empty-checksums"')
        self.assertEqual(pool.start_task.user_identity.auto_user.elevation_level, 'admin')
        self.assertTrue(pool.start_task.wait_for_success)

    def test_batch_extensions_packagemanager_with_existing_starttask(self):
        pool = models.ExtendedPoolParameter(
            id="testpool",
            virtual_machine_configuration=models.VirtualMachineConfiguration(
                image_reference=models.ImageReference(
                    publisher="Canonical",
                    offer="UbuntuServer",
                    sku="15.10",
                    version="latest"
                ),
                node_agent_sku_id="batch.node.debian 8"
            ),
            vm_size="STANDARD_A1",
            target_dedicated_nodes="10",
            enable_auto_scale=False,
            start_task=models.StartTask(
                command_line="/bin/bash -c 'set -e; set -o pipefail; nodeprep-cmd' ; wait",
                user_identity=models.UserIdentity(
                    auto_user=models.AutoUserSpecification(elevation_level='admin')
                ),
                wait_for_success=True,
                resource_files=[
                    models.ExtendedResourceFile(
                        source=models.FileSource(file_group='abc'),
                        file_path='nodeprep-cmd'
                    )
                ]
            ),
            package_references=[
                models.AptPackageReference("ffmpeg"),
                models.AptPackageReference("apache2", "12.34")
            ]
        )
        commands = [utils.process_pool_package_references(pool)]
        pool.start_task = models.StartTask(**utils.construct_setup_task(
            pool.start_task, commands,
            pool_utils.PoolOperatingSystemFlavor.LINUX))
        self.assertEqual(pool.vm_size, 'STANDARD_A1')
        # TODO: Shell escape
        #self.assertEqual(
        #    pool.start_task.command_line,
        #    "/bin/bash -c 'apt-get update;apt-get install -y "
        #    "ffmpeg;apt-get install -y apache2=12.34;/bin/bash -c "
        #    "'\\''set -e; set -o pipefail; nodeprep-cmd'\\'' ; wait'")
        self.assertEqual(pool.start_task.user_identity.auto_user.elevation_level, 'admin')
        self.assertTrue(pool.start_task.wait_for_success)
        self.assertEqual(len(pool.start_task.resource_files), 1)

    def test_batch_extensions_packagemanager_taskfactory(self):
        job = Mock(
            job_preparation_task=None,
            task_factory=models.ParametricSweepTaskFactory(
                parameter_sets=[models.ParameterSet(1, 2), models.ParameterSet(3, 5)],
                repeat_task=models.RepeatTask(
                    command_line="cmd {0}.mp3 {1}.mp3",
                    package_references=[
                        models.AptPackageReference("ffmpeg"),
                        models.AptPackageReference("apache2", "12.34")
                    ]
                )
            )
        )
        collection = utils.expand_task_factory(job, None)
        commands = []
        commands.append(utils.process_task_package_references(
            collection, pool_utils.PoolOperatingSystemFlavor.LINUX))
        commands.append(None)
        job.job_preparation_task = models.JobPreparationTask(**utils.construct_setup_task(
            job.job_preparation_task, commands,
            pool_utils.PoolOperatingSystemFlavor.LINUX))
        self.assertIsNone(job.task_factory)
        self.assertEqual(job.job_preparation_task.command_line,
                         '/bin/bash -c \'apt-get update;apt-get install '
                         '-y ffmpeg;apt-get install -y apache2=12.34\'')
        self.assertEqual(job.job_preparation_task.user_identity.auto_user.elevation_level, 'admin')
        self.assertEqual(job.job_preparation_task.wait_for_success, True)

    def test_batch_extensions_starttask_without_packagemanager(self):
        job = Mock(
            job_preparation_task=None,
            task_factory=models.ParametricSweepTaskFactory(
                parameter_sets=[models.ParameterSet(1, 2), models.ParameterSet(3, 5)],
                repeat_task=models.RepeatTask("cmd {0}.mp3 {1}.mp3")
            )
        )
        collection = utils.expand_task_factory(job, None)
        commands = []
        commands.append(utils.process_task_package_references(
            collection, pool_utils.PoolOperatingSystemFlavor.LINUX))
        commands.append(None)
        job.job_preparation_task = utils.construct_setup_task(
            job.job_preparation_task, commands,
            pool_utils.PoolOperatingSystemFlavor.LINUX)
        self.assertIsNone(job.task_factory)
        self.assertIsNone(job.job_preparation_task)

    def test_batch_extensions_bad_packagemanager_configuration(self):
        pool = models.ExtendedPoolParameter(
            id="testpool",
            virtual_machine_configuration=models.VirtualMachineConfiguration(
                image_reference=models.ImageReference(
                    publisher="Canonical",
                    offer="UbuntuServer",
                    sku="15.10",
                    version="latest"
                ),
                node_agent_sku_id="batch.node.debian 8"
            ),
            vm_size="STANDARD_A1",
            target_dedicated_nodes="10",
            enable_auto_scale=False,
            package_references=[
                models.AptPackageReference("ffmpeg"),
                models.AptPackageReference("apache2", "12.34")
            ]
        )
        pool.package_references[0].type = "newPackage"
        with self.assertRaises(ValueError):
            utils.process_pool_package_references(pool)

        pool.package_references[0] = models.ChocolateyPackageReference("ffmpeg")
        with self.assertRaises(ValueError):
            utils.process_pool_package_references(pool)

        pool.package_references = [models.AptPackageReference("ffmpeg", "12.34")]
        pool.package_references[0].id = None
        with self.assertRaises(ValueError):
            utils.process_pool_package_references(pool)


    def test_batch_extensions_validate_job_requesting_app_template(self):
        # Should do nothing for a job not using an application template'
        job = models.ExtendedJobParameter('jobid', None)

        # Should throw an error if job does not specify template location
        with self.assertRaises(TypeError):
            appTemplate = models.ApplicationTemplateInfo(None)

        # Should throw an error if the template referenced by the job does not
        # exist
        with self.assertRaises(ValueError):
            appTemplate = models.ApplicationTemplateInfo(self.static_apptemplate_path + '.notfound')

        # Should throw an error if job uses property reserved for application
        # template use
        app_template = models.ApplicationTemplateInfo(self.static_apptemplate_path)
        with self.assertRaises(ValueError):
            job = models.ExtendedJobParameter('jobid', None, application_template_info=app_template,
                                          uses_task_dependencies=True)

    def test_batch_extensions_merge_metadata(self):
        # should return empty metadata when no metadata supplied
        alpha = None
        beta = None
        result = utils._merge_metadata(alpha, beta)  # pylint: disable=protected-access
        self.assertEqual(result, [])

        # should return base metadata when only base metadata supplied
        alpha = [
            {
                'name': 'name',
                'value': 'Adam'
            },
            {
                'name': 'age',
                'value': 'old'
            }]
        beta = None
        result = utils._merge_metadata(alpha, beta)  # pylint: disable=protected-access
        self.assertEqual(result, alpha)

        # should return more metadata when only more metadata supplied
        alpha = None
        beta = [models.MetadataItem(
            name='gender',
            value='unspecified'
        )]
        result = utils._merge_metadata(alpha, beta)  # pylint: disable=protected-access
        self.assertEqual(result, [{'name':'gender', 'value':'unspecified'}])

        # should throw an error if the two collections overlap
        alpha = [
            {
                'name': 'name',
                'value': 'Adam'
            },
            {
                'name': 'age',
                'value': 'old'
            }]
        beta = [
            models.MetadataItem(
                name='name',
                value='Brian'
            ),
            models.MetadataItem(
                name='gender',
                value='unspecified'
            )]
        with self.assertRaises(ValueError) as ve:
            utils._merge_metadata(alpha, beta)  # pylint: disable=protected-access
        self.assertIn('name', ve.exception.args[0],
                      'Expect metadata \'name\' to be mentioned')

        # should return merged metadata when there is no overlap
        alpha = [
            {
                'name': 'name',
                'value': 'Adam'
            },
            {
                'name': 'age',
                'value': 'old'
            }]
        beta = [
            models.MetadataItem(
                name='gender',
                value='unspecified'
            )]
        expected = [
            {
                'name': 'name',
                'value': 'Adam'
            },
            {
                'name': 'age',
                'value': 'old'
            },
            {
                'name': 'gender',
                'value': 'unspecified'
            }]
        result = utils._merge_metadata(alpha, beta)  # pylint: disable=protected-access
        self.assertEqual(result, expected)

    def test_batch_extensions_generate_job(self):
        # should throw an error if the generated job uses a property reserved for template use
        job = {
            'id': 'jobid',
            'applicationTemplateInfo': {
                'filePath': self.static_apptemplate_path
            },
            'usesTaskDependencies': True
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_generated_job(job)  # pylint: disable=protected-access
        self.assertIn('applicationTemplateInfo', ve.exception.args[0],
                      'Expect property \'applicationTemplateInfo\' to be mentioned')

        # should throw an error if the template uses a property reserved for
        # use by the job
        template = {
            'usesTaskDependencies': True,
            'displayName': 'display this name'
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_generated_job(template)  # pylint: disable=protected-access
        self.assertIn('displayName', ve.exception.args[0],
                      'Expect property \'displayName\' to be mentioned')

        # should throw an error if the template uses a property not recognized
        template = {
            'usesTaskDependencies': True,
            'vendor': 'origin'
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_generated_job(template)  # pylint: disable=protected-access
        self.assertIn('vendor', ve.exception.args[0],
                      'Expect property \'vendor\' to be mentioned')

    def test_batch_extensions_template_merging(self):
        # pylint: disable=too-many-statements
        # should do nothing when no application template is required

        # should throw error if no filePath supplied for application template
        job = models.ExtendedJobParameter("jobid", None,
            application_template_info=models.ApplicationTemplateInfo(self.static_apptemplate_path))
        job.application_template_info.file_path = None
        with self.assertRaises(ValueError):
            utils.expand_application_template(job, self._deserialize)

        # should merge a template with no parameters
        job = models.ExtendedJobParameter("jobid", None,
            application_template_info=models.ApplicationTemplateInfo(self.static_apptemplate_path))
        result = utils.expand_application_template(job, self._deserialize)
        self.assertIsNotNone(job.job_manager_task,
            "expect the template to have provided jobManagerTask.")

        # should preserve properties on the job when expanding the template
        job = models.ExtendedJobParameter("importantjob", None,
            priority=500,
            application_template_info=models.ApplicationTemplateInfo(self.static_apptemplate_path))
        
        result = utils.expand_application_template(job, self._deserialize)
        self.assertEqual(job.id, 'importantjob')
        self.assertEqual(job.priority, 500)

        # should use parameters from the job to expand the template
        job = models.ExtendedJobParameter("parameterJob", None,
            application_template_info=models.ApplicationTemplateInfo(
                self.apptemplate_with_params_path,
                parameters={
                    'blobName': "music.mp3",
                    'keyValue': "yale"
                }))
        job_ref = models.ExtendedJobParameter(**job.__dict__)
        utils.expand_application_template(job, self._deserialize)
        self.assertIsNone(job.application_template_info)
        self.assertEqual(job.job_manager_task.resource_files[1].file_path,
                         job_ref.application_template_info.parameters['blobName'])
        self.assertEqual(job.metadata[0].value,
                         job_ref.application_template_info.parameters['keyValue'])

        # should throw an error if any parameter has an undefined type
        untyped_parameter_path = os.path.join(self.data_dir,
            'batch-applicationTemplate-untypedParameter.json')
        job = models.ExtendedJobParameter("parameterJob", None,
            application_template_info=models.ApplicationTemplateInfo(
                untyped_parameter_path,
                parameters={
                    'blobName': "music.mp3",
                    'keyValue': "yale"
                }))
        with self.assertRaises(ValueError) as ve:
            utils.expand_application_template(job, self._deserialize)
        self.assertIn('blobName', ve.exception.args[0],
                      'Expect parameter \'blobName\' to be mentioned')

        # should not have an applicationTemplateInfo property on the expanded job
        job = models.ExtendedJobParameter("importantjob", None,
            priority=500,
            application_template_info=models.ApplicationTemplateInfo(self.static_apptemplate_path))
        utils.expand_application_template(job, self._deserialize)
        self.assertIsNone(job.application_template_info)

        # should not copy templateMetadata to the expanded job
        job = models.ExtendedJobParameter("importantjob", None,
            priority=500,
            application_template_info=models.ApplicationTemplateInfo(self.static_apptemplate_path))
        utils.expand_application_template(job, self._deserialize)
        self.assertFalse(hasattr(job, 'template_metadata'))

        # should not have a parameters property on the expanded job
        job = models.ExtendedJobParameter("importantjob", None,
            priority=500,
            application_template_info=models.ApplicationTemplateInfo(self.static_apptemplate_path))
        utils.expand_application_template(job, self._deserialize)
        self.assertFalse(hasattr(job, 'parameters'))

        # should throw error if application template specifies \'id\' property
        templateFilePath = os.path.join(self.data_dir,
            'batch-applicationTemplate-prohibitedId.json')
        job = models.ExtendedJobParameter("jobid", None,
            application_template_info=models.ApplicationTemplateInfo(templateFilePath))
        with self.assertRaises(ValueError) as ve:
            utils.expand_application_template(job, self._deserialize)
        self.assertIn('id', ve.exception.args[0], 'Expect property \'id\' to be mentioned')

        # should throw error if application template specifies \'poolInfo\' property
        templateFilePath = os.path.join(self.data_dir,
            'batch-applicationTemplate-prohibitedPoolInfo.json')
        job = models.ExtendedJobParameter("jobid", None,
            application_template_info=models.ApplicationTemplateInfo(templateFilePath))
        with self.assertRaises(ValueError) as ve:
            utils.expand_application_template(job, self._deserialize)
        self.assertIn('poolInfo', ve.exception.args[0],
                      'Expect property \'poolInfo\' to be mentioned')

        # should throw error if application template specifies \'applicationTemplateInfo\' property
        templateFilePath = os.path.join(self.data_dir,
            'batch-applicationTemplate-prohibitedApplicationTemplateInfo.json')
        job = models.ExtendedJobParameter("jobid", None,
            application_template_info=models.ApplicationTemplateInfo(templateFilePath))
        with self.assertRaises(ValueError) as ve:
            utils.expand_application_template(job, self._deserialize)
        self.assertIn('applicationTemplateInfo', ve.exception.args[0],
                      'Expect property \'applicationTemplateInfo\' to be mentioned')

        # should throw error if application template specifies \'priority\' property', function(_){
        templateFilePath = os.path.join(self.data_dir,
            'batch-applicationTemplate-prohibitedPriority.json')
        job = models.ExtendedJobParameter("jobid", None,
            application_template_info=models.ApplicationTemplateInfo(templateFilePath))
        with self.assertRaises(ValueError) as ve:
            utils.expand_application_template(job, self._deserialize)
        self.assertIn('priority', ve.exception.args[0],
                      'Expect property \'priority\' to be mentioned')

        # should throw error if application template specifies unrecognized property
        templateFilePath = os.path.join(self.data_dir,
            'batch-applicationTemplate-unsupportedProperty.json')
        job = models.ExtendedJobParameter("jobid", None,
            application_template_info=models.ApplicationTemplateInfo(templateFilePath))
        with self.assertRaises(ValueError) as ve:
            utils.expand_application_template(job, self._deserialize)
        self.assertIn('fluxCapacitorModel', ve.exception.args[0],
                      'Expect property \'fluxCapacitorModel\' to be mentioned')

        # should include metadata from original job on generated job
        job = models.ExtendedJobParameter("importantjob", None,
            priority=500,
            metadata=[models.MetadataItem('author', 'batman')],
            application_template_info=models.ApplicationTemplateInfo(
                self.apptemplate_with_params_path,
                parameters={
                    'blobName': 'henry',
                    'keyValue': 'yale'
                }))
        
        utils.expand_application_template(job, self._deserialize)
        self.assertTrue(job.metadata)
        self.assertTrue([m for m in job.metadata if m.name=='author' and m.value=='batman'])

        # should include metadata from template on generated job
        job = models.ExtendedJobParameter("importantjob", None,
            priority=500,
            metadata=[models.MetadataItem('author', 'batman')],
            application_template_info=models.ApplicationTemplateInfo(
                self.apptemplate_with_params_path,
                parameters={
                    'blobName': 'henry',
                    'keyValue': 'yale'
                }))
        
        utils.expand_application_template(job, self._deserialize)
        self.assertTrue(job.metadata)
        self.assertTrue([m for m in job.metadata if m.name=='myproperty' and m.value=='yale'])

        # should add a metadata property with the template location
        job = models.ExtendedJobParameter("importantjob", None,
            priority=500,
            application_template_info=models.ApplicationTemplateInfo(self.static_apptemplate_path))
        utils.expand_application_template(job, self._deserialize)
        self.assertTrue(job.metadata)
        self.assertTrue([m for m in job.metadata 
                         if m.name=='az_batch:template_filepath' and m.value==self.static_apptemplate_path])

        # should not allow the job to use a metadata property with our reserved prefix
        job = models.ExtendedJobParameter("importantjob", None,
            priority=500,
            metadata=[models.MetadataItem('az_batch:property', 'something')],
            application_template_info=models.ApplicationTemplateInfo(
                self.static_apptemplate_path))

        with self.assertRaises(ValueError) as ve:
            utils.expand_application_template(job, self._deserialize)
        self.assertIn('az_batch:property', ve.exception.args[0],
                      'Expect metadata \'az_batch:property\' to be mentioned')

    def test_batch_extensions_validate_parameter_usage(self):
        # should throw an error if no value is provided for a parameter without
        # a default
        parameters = {}
        definitions = {
            'name': {
                'type': 'string'
            }
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_parameter_usage(parameters, definitions)  # pylint: disable=protected-access
        self.assertIn('name', ve.exception.args[0],
                      'Expect parameter \'name\' to be mentioned')

        # should throw an error if the value provided for an int parameter is
        # not type compatible
        parameters = {
            'age': 'eleven'
        }
        definitions = {
            'age': {
                'type': 'int'
            }
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_parameter_usage(parameters, definitions)  # pylint: disable=protected-access
        self.assertIn('age', ve.exception.args[0],
                      'Expect parameter \'age\' to be mentioned')

        # should not throw an error if the default value provided for an int
        # parameter is used
        parameters = {}
        definitions = {
            'age': {
                'type': 'int',
                'defaultValue': 11
            }
        }
        utils._validate_parameter_usage(parameters, definitions)  # pylint: disable=protected-access

        # should not throw an error if the default value provided for an int
        # parameter is not an integer
        parameters = {}
        definitions = {
            'age': {
                'type': 'int',
                'defaultValue': 'eleven'
            }
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_parameter_usage(parameters, definitions)  # pylint: disable=protected-access
        self.assertIn('age', ve.exception.args[0], 'Expect parameter \'age\' to be mentioned')

        # should throw an error if the value provided for an bool parameter is
        # not type compatible
        parameters = {
            'isMember': 'frog'
        }
        definitions = {
            'isMember': {
                'type': 'bool'
            }
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_parameter_usage(parameters, definitions)  # pylint: disable=protected-access
        self.assertIn('isMember', ve.exception.args[0],
                      'Expect parameter \'isMember\' to be mentioned')

        # should throw an error if a value is provided for a non-existing
        # parameter
        parameters = {
            'membership': 'Gold'
        }
        definitions = {
            'customerType': {
                'type': 'string',
                'defaultValue': 'peasant'
            }
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_parameter_usage(parameters, definitions)  # pylint: disable=protected-access
        self.assertIn('membership', ve.exception.args[0],
                      'Expect parameter \'membership\' to be mentioned')

        # should accept having no job parameters if there are no template
        # parameters
        parameters = None
        definitions = None
        utils._validate_parameter_usage(parameters, definitions)  # pylint: disable=protected-access
        # Pass implied by no Error

        # should accept having no job parameters if all template parameters
        # have defaults
        parameters = None
        definitions = {
            'customerType': {
                'type': 'string',
                'defaultValue': 'peasant'
            }
        }
        utils._validate_parameter_usage(parameters, definitions)  # pylint: disable=protected-access
        # Pass implied by no Error

        # should throw an error if a parameter does not declare a specific type
        definitions = {
            'name': {
                'defaultValue': 'Mouse'
            }
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_parameter_usage(None, definitions)  # pylint: disable=protected-access
        self.assertIn('name', ve.exception.args[0],
                      'Expect parameter \'name\' to be mentioned')

        # should throw an error if a parameter does not declare a supported
        # type
        definitions = {
            'name': {
                'defaultValue': 'Mouse',
                'type': 'dateTime'
            }
        }
        with self.assertRaises(ValueError) as ve:
            utils._validate_parameter_usage(None, definitions)  # pylint: disable=protected-access
        self.assertIn('name', ve.exception.args[0],
                      'Expect parameter \'name\' to be mentioned')

    def test_batch_extensions_transform_resourcefiles_from_filegroup(self):
        resource = models.ExtendedResourceFile(
            file_path=None,
            source=models.FileSource(file_group='data'))
        blobs = [
            {'filePath': 'data1.txt', 'url': 'https://blob.fgrp-data/data1.txt'},
            {'filePath': 'data2.txt', 'url': 'https://blob.fgrp-data/data2.txt'}
        ]
        resources = file_utils.convert_blobs_to_resource_files(blobs, resource)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].blob_source, "https://blob.fgrp-data/data1.txt")
        self.assertEqual(resources[0].file_path, "data1.txt")
        self.assertEqual(resources[1].blob_source, "https://blob.fgrp-data/data2.txt")
        self.assertEqual(resources[1].file_path, "data2.txt")

        resource = {
            'source': {'fileGroup': 'data', 'prefix': 'data1.txt'},
            'filePath': 'localFile'
        }
        resource = models.ExtendedResourceFile(
            source=models.FileSource(file_group='data', prefix='data1.txt'),
            file_path='localFile')
        blobs = [
            {'filePath': 'data1.txt', 'url': 'https://blob.fgrp-data/data1.txt'}
        ]
        resources = file_utils.convert_blobs_to_resource_files(blobs, resource)
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].blob_source, "https://blob.fgrp-data/data1.txt")
        self.assertEqual(resources[0].file_path, "localFile")

        resource = models.ExtendedResourceFile(
            source=models.FileSource(file_group='data', prefix='data1'),
            file_path='localFile')
        blobs = [
            {'filePath': 'data1.txt', 'url': 'https://blob.fgrp-data/data1.txt'}
        ]
        resources = file_utils.convert_blobs_to_resource_files(blobs, resource)
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].blob_source, "https://blob.fgrp-data/data1.txt")
        self.assertEqual(resources[0].file_path, "localFile/data1.txt")

        resource = models.ExtendedResourceFile(
            source=models.FileSource(file_group='data', prefix='subdir/data'),
            file_path='localFile')
        blobs = [
            {'filePath': 'subdir/data1.txt',
             'url': 'https://blob.fgrp-data/subdir/data1.txt'},
            {'filePath': 'subdir/data2.txt',
             'url': 'https://blob.fgrp-data/subdir/data2.txt'}
        ]
        resources = file_utils.convert_blobs_to_resource_files(blobs, resource)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].blob_source,
                         "https://blob.fgrp-data/subdir/data1.txt")
        self.assertEqual(resources[0].file_path, "localFile/subdir/data1.txt")
        self.assertEqual(resources[1].blob_source,
                         "https://blob.fgrp-data/subdir/data2.txt")
        self.assertEqual(resources[1].file_path, "localFile/subdir/data2.txt")

        resource = models.ExtendedResourceFile(
            source=models.FileSource(file_group='data', prefix='subdir/data'),
            file_path='localFile/')
        blobs = [
            {'filePath': 'subdir/data1.txt', 'url':
             'https://blob.fgrp-data/subdir/data1.txt'}
        ]
        resources = file_utils.convert_blobs_to_resource_files(blobs, resource)
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].blob_source,
                         "https://blob.fgrp-data/subdir/data1.txt")
        self.assertEqual(resources[0].file_path, "localFile/subdir/data1.txt")

        resource = {
            'source': {'fileGroup': 'data', 'prefix': 'subdir/data'},
        }
        resource = models.ExtendedResourceFile(
            file_path=None,
            source=models.FileSource(file_group='data', prefix='subdir/data'))
        blobs = [
            {'filePath': 'subdir/data1.txt',
             'url': 'https://blob.fgrp-data/subdir/data1.txt'},
            {'filePath': 'subdir/more/data2.txt',
             'url': 'https://blob.fgrp-data/subdir/more/data2.txt'}
        ]
        resources = file_utils.convert_blobs_to_resource_files(blobs, resource)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].blob_source,
                         "https://blob.fgrp-data/subdir/data1.txt")
        self.assertEqual(resources[0].file_path, "subdir/data1.txt")
        self.assertEqual(resources[1].blob_source,
                         "https://blob.fgrp-data/subdir/more/data2.txt")
        self.assertEqual(resources[1].file_path, "subdir/more/data2.txt")
