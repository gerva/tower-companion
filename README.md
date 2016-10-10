Tower companion
===============

Tower companion is a set of utilities to start and monitor Ansible tower jobs
from the command line.

The main reason for this tool is to extend tower-cli so it provides a real time
output of the requested job.

Tower companion provides the following command line scripts:

-  [kick](#kick)
-  [monitor](#monitor)
-  [kick_and_monitor](#kick_and_monitor)
-  [ad_hoc](#ad_hoc)
-  [ad_hoc_and_monitor](#ad_hoc_and_monitor)


Installation
------------
Tower companion is avaliable as a package on PyPi
To install tower-companion execute: ``pip install tower-companion``


configuration
-------------
This tool uses ansible tower cli, and expects you to have a ``~/.tower-cli.cfg``
in your home directory or in any other directory describe in the ansible
tower-cli configuration section. Please refer to the [ansible-tower-cli
documentation page](https://github.com/ansible/tower-cli)



reckless mode
-------------
If you use valid SSL certificates, skip this section. If your ansible tower
instance SSL certificates are not valid, you might want to enter into reckless
mode. This option supresses the SSL issue warnings in the ouptut messasages.
It's just a workaround you should use valid certificates instead of activating
this option.

If you *really* want to enter into reckless mode, add the following line in your
`~/.tower-cli.cfg` file.

    ...
    reckless_mode: yes


### <a name="kick"></a>
kick
----
This script starts an Ansible tower job template and returns immediatly.

Params:

-  template-name: Ansible tower template name
-  extra-vars: (if any)

Returns:

-  exit code 0 if the job template has been started successfully
-  exit code 1 if any issues

usage:

	kick --help
	Usage: kick [OPTIONS]

	  Start an ansible tower job from the command line

	Options:
	  --template-name TEXT  Job template name  [required]
	  --extra-vars TEXT     Extra variables
	  --help                Show this message and exit.

example:

    $ kick --template-name 'Backend jboss deployment' --extra-vars 'version: 2.3'
    Started job: 12345



note:
this requires a template job named: "Backend jboss deployment" in your Ansible
tower instance.


### <a name="monitor"></a>
monitor
-------
This script takes a job id as paramter and shows the Ansible tower job output
until the job is not complete (monitor blocks until the job is not complete)

Params:

-  job-id: ansible tower job id to monitor
-  output-format: can be txt or ansi. Use 'ansi' (default) for a colorful output

Returns:

-  exit code 0 if the job comleted without errors
-  exit code 1 if any issues

usage:

	monitor --help
	Usage: monitor [OPTIONS]

	Monitor the execution of an ansible tower job

	Options:
	  --job-id TEXT               Job id to monitor  [required]
	  --output-format [ansi|txt]  output format
	  --help                      Show this message and exit.

example:

    $ monitor --job-id 12345
    Vault password:
    PLAY [all] ***************************************

    TASK [setup] *************************************
    ok: [jboss-01]
    ok: [jboss-02]
    ...
    PLAY RECAP ***************************************
    jboss-01: ok=20    changed=1    unreachable=0    failed=0
    jboss-02: ok=20    changed=1    unreachable=0    failed=0

    you can download the full output from:
    https://<ansible tower instance>/api/v1/jobs/12345/stdout/?format=txt_download


### <a name="kick_and_monitor"></a>
kick_and_monitor
----------------
This is probably what you want to use it starts an ansible tower job and shows
the output in real time until the job is not complete (or when it fails)

Params:

-  job-id: ansible tower job id to monitor
-  output-format: can be txt or ansi. Use 'ansi' (default) for a colorful output

Returns:

-  exit code 0 if the job comleted without errors
-  exit code 1 if any issues

usage:

	Usage: kick_and_monitor [OPTIONS]

	  Trigger an ansible tower job and monitor its execution. In case of error
	  it returns a bad exit code.

	Options:
	  --template-name TEXT        Job template name  [required]
	  --extra-vars TEXT           Extra variables
	  --output-format [ansi|txt]  output format
	  --help                      Show this message and exit.

example:

    $ kick_and_monitor --template-name 'Backend jboss deployment' --extra-vars 'version: 2.3'
    Vault password:
    PLAY [all] ***************************************

    TASK [setup] *************************************
    ok: [jboss-01]
    ok: [jboss-02]
    ...
    PLAY RECAP ***************************************
    jboss-01: ok=20    changed=1    unreachable=0    failed=0
    jboss-02: ok=20    changed=1    unreachable=0    failed=0

    you can download the full output from:
    https://<ansible tower instance>/api/v1/jobs/12346/stdout/?format=txt_download

### <a name="ad_hoc"></a>
ad_hoc
----
This script starts an Ansible tower ad-hoc command and returns immediatly.

Params:

-  inventory: Inventory to run on
-  machine_credential: SSH credentials name
-  module_name: Ansible module to run
-  job_type: Type of job so execute
-  module_args: Arguments for the selected module
-  limit: Limit to hosts
-  job_explanation: Job description
-  verbose: Verbose mode
-  become: Become a superuser

Returns:

-  exit code 0 if the job template has been started successfully
-  exit code 1 if any issues

usage:

    ad_hoc --help
    Usage: ad_hoc [OPTIONS]

    Trigger an ansible tower ad hoc job and monitor its execution. In case of error it returns a bad exit code.

    Options:
      --inventory TEXT           Inventory to run on  [required]
      --machine-credential TEXT  SSH credentials name  [required]
      --module-name TEXT         Ansible module to run  [required]
      --job-type [run|check]     Type of job so execute
      --module-args TEXT         Arguments for the selected module
      --limit TEXT               Limit to hosts
      --job-explanation TEXT     Job description
      --verbose                  Verbose mode
      --become                   Become root
      --help                     Show this message and exit.

example:

    $ ad_hoc --inventory jboss                          \
             --machine-credential "Ansible Machine SSH" \
             --module-name command                      \
             --module-args "ls -l /"                    \
             --limit jboss-01                           \
             --job-explanation "This is the first job from ad_hoc tower companion"
    Started job: 20894


### <a name="ad_hoc_and_monitor"></a>
ad_hoc_and_monitor
----------------
You use this ad-hoc functionality, if you want to fire a command on a bunch of
selected machines or on a single machine. Like for the kick_and_monitor the
output will be printed in real time

Params:

-  inventory: Inventory to run on
-  machine_credential: SSH credentials name
-  module_name: Ansible module to run
-  job_type: Type of job so execute
-  module_args: Arguments for the selected module
-  limit: Limit to hosts
-  job_explanation: Job description
-  verbose: Verbose mode
-  become: Become a superuser
-  output-format: can be txt or ansi. Use 'ansi' (default) for a colorful output

Returns:

-  exit code 0 if the job comleted without errors
-  exit code 1 if any issues

usage:

    Usage: ad_hoc_and_monitor [OPTIONS]

    Trigger an ansible tower ad hoc job and monitor its execution. In case of
    error it returns a bad exit code.

    Options:
      --inventory TEXT            Inventory to run on  [required]
      --machine-credential TEXT   SSH credentials name  [required]
      --module-name TEXT          Ansible module to run  [required]
      --job-type [run|check]      Type of job so execute
      --module-args TEXT          Arguments for the selected module
      --limit TEXT                Limit to hosts
      --job-explanation TEXT      Job description
      --verbose                   Verbose mode
      --become                    Become root
      --output-format [ansi|txt]  output format
      --help                      Show this message and exit.

example:

    $ ad_hoc_and_monitor --inventory jboss                          \
                         --machine-credential "Ansible Machine SSH" \
                         --module-name command                      \
                         --module-args "ls -l /"                    \
                         --limit jboss-01                           \
                         --job-explanation "This is the second job from ad_hoc tower companion"
    job id: 20895
    Waiting for results...

    jboss-01 | SUCCESS | rc=0 >>
    total 36
    lrwxrwxrwx.   1 root root    7 Dec 29  2015 bin -> usr/bin
    dr-xr-xr-x.   4 root root 4096 Sep 28 00:48 boot
    drwxr-xr-x.  20 root root 3400 Sep 29 07:57 dev
    drwxr-xr-x.  94 root root 8192 Sep 28 02:38 etc
    drwxr-xr-x.  12 root root 4096 Sep 19 01:25 home

    you can download the full output from:
    https://<ansible tower instance>/api/v1/jobs/20895/stdout/?format=txt_download
