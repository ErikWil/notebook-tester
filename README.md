# notebook-tester
Using jupyter notebooks as testing environment

## The idea

Jupyter notebooks are a great way to tinker with code, explore and do testing. On the other hand it can be used
to document and learn how code and API's are designed.

The idea here is a bit similar to [doctest](https://docs.python.org/3/library/doctest.html). You run your notebook
on your code after changes. If the output has changed, the code has changed.

## Preparing code for testing

Preparing code for testing can be done in two simple steps
1. Start the first line of the code cell you want to include in you testing with `#test-case:`*name*
2. run the command `notebooktester init mynotebook.ipynb`

## Running tests

Now - assuming you have made changes in your code base and want to test if the changes have any side effects you can run 
the command `notebooktester test mynotebook.ipynb`. This will load the notebook and 


