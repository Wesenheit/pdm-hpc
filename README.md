# pdm-hpc

Virtual enviroments are the usuall way to version and control packages used 
in the real-world dev work. However, this is not the usuall way to work on HPC clusters. In such cases
we are usually beeing provided with certain versions of packages that are already compiled and 
tested against clusters specific software (notable cases include `mpi4py` or `pytorch`, packages linked 
against the specific MPI version that is cluster-optimized). Current tools do not provide any 
way to reliably verify content provied in pyproject.toml against installed versions. This 
plugin is designed to bring down this barrier and bring modern tools to HPC.

[!WARNING]
To use the plugin remember to setup pdm project so it can inherit system packages!

## Usage
To install the plugin we can specify a very simple example:

```
[project]
name = "Test"
version = "0.1.0"
requires-python = ">3.10"
dependencies = [
    "requests>=2.30",
    "numpy>2.0",
]

[tool.pdm.external-dependencies]
packages = ["numpy", "torch"]

[tool.pdm]
plugins = ["pdm-hpc @ git+https://github.com/Wesenheit/pdm-hpc.git"]
```
We have installed our plugin and we are requesting few libraries. We are telling our system 
that we would like to use `numpy` and `pytorch` from the system library.

If there is no system library for `numpy` we will get error when using `pdm install` (during lock creation):
```
>>> numpy:
      requested:  >2.0
      system:     not found
[RuntimeError]:
External dependency validation failed:
  - numpy: not found in system Python
```
Now we can load a module enviromental file that provides us with `numpy 1.26.4`. Now when we run 
we will get 
```
>>> numpy:
      requested:  >2.0
      system:     1.26.4
[RuntimeError]:
External dependency validation failed:
  - numpy: system has 1.26.4 but >2.0 is required
```
Our numpy version is no good, let's decrease the version requirements to >1.0. We finally have

```
>>> numpy:
      requested:  >1.0
      system:     1.26.4
      OK: pinning numpy==1.26.4
Changes are written to pdm.lock.
  0:00:01 🔒 Lock successful.
Synchronizing working set with resolved packages: 5 to add, 0 to update, 0 to remove

  ✔ Install certifi 2026.2.25 successful
  ✔ Install urllib3 2.6.3 successful
  ✔ Install requests 2.32.5 successful
  ✔ Install charset-normalizer 3.4.4 successful
  ✔ Install SpackTest 0.1.0 successful

  0:00:00 🎉 All complete! 5/5

```
This allows us to finally proceed with the instalation. Keep in mind that this creates `pdm.lock` file with 
`numpy` version specified by the system-resolved version. This is really important when moving off-cluster.
```
>>> numpy:
      requested:  >1.0
      system:     1.26.4
      OK: pinning numpy==1.26.4
>>> torch:
      requested:  any
      system:     2.9.0
      OK: pinning torch==2.9.0
```
we will get `torch` version saved so we can use it to reproduce results out of cluster.
