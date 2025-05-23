# Upload File XBlock

An OpenEdX XBlock that allows students to upload files as a response.


## Development

We use the xblock workbench here: https://github.com/openedx/xblock-sdk

Follow the instructions to install and create it and then install this XBlock into
the python virtual environment:

```sh
pip install --upgrade --force-reinstall  git+https://github.com/imsimbi-training/xblock-uploadfile
```

or for local dev:

```sh
pip install --upgrade --force-reinstall  -e ../xblock-uploadfile
```


Run the workbench in `xblock-sdk`:

```
python manage.py runserver
```

The XBlock should be available in the workbench

Any cell that has a class `input` will allow the student to enter text
(using an html `<textarea>`). A prompt should be given for each input as the inner text.
A `name` attribute is used for referencing the response in the state (see below).

A tag with a `repeat` class can be replicated by the student, allowing them to provide
multiple responses. This is explained below.

The rest of the HTML is used for static layout of the uploadfile and any valid html
can be used.

## State

The state will be stored with this structure:

```json
{
    "file_url": "https://filestore.com/files/file1.pdf",
    "submitted": true,
}
```
