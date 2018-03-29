.. _run_colmto:

Usage
=====

You can run CoLMTO directly as a script, providing your local python install directory is in your ``$PATH``:
Keep in mind to set ``SUMO_HOME`` accordingly:

.. code-block:: bash

    export SUMO_HOME=~/colmto/sumo/sumo # adjust accordingly
    colmto --runs 1

If you have not installed CoLMTO in the previous section, run it inside the project directory as module.

.. code-block:: bash

    cd colmto
    python3 -m colmto --runs 1

Upon first start CoLMTO creates `YAML <https://en.wikipedia.org/wiki/YAML>`_ formatted default configurations and its log file in ``~/.colmto/``:

.. code-block:: bash

    ~/.colmto/
    ├── colmto.log
    ├── runconfig.yaml
    ├── scenarioconfig.yaml
    └── vtypesconfig.yaml

Further help on command line options can be obtained by running

.. code-block:: bash

    colmto --help