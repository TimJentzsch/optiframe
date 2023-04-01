# Optiframe [![PyPI](https://img.shields.io/pypi/v/optiframe)](https://pypi.org/project/optiframe/) [![PyPI - License](https://img.shields.io/pypi/l/optiframe)](LICENSE)

Optiframe is an **opti**mization **frame**work for writing mixed integer programs (MIPs).

It allows you to structure your MIPs in a way that allows clear separation of concerns,
high modularity and testability.

## Core Concepts

- The optimization process is divided into multiple **steps** which are clearly separated:
  1. **Validation** allows you to validate the input data.
  2. **MIP building** allows you to modify the MIP to define the optimization problem.
  3. **Solving** is a pre-defined step that obtains an optimal solution for the problem.
  4. **Solution extraction** allows you to process the variable values of the solution into something more meaningful.
- **Tasks** are the core components that allow you to implement functionality for each step.
  - The constructor of a task allows you to define *dependencies* for that task,
    which are automatically injected by the optimizer based on their type annotation.
  - The **execute** method allows you to implement the functionality.
    It may return data which can then be used by other tasks as a dependency.
- **Packages** combine tasks that belong together.
    Each package must contain a task for building the MIP and can additionally contain tasks
    for validation and solution extraction.
    The packages are what makes Optiframe so modular:
    You can define extensions of a problem in a separate package and only include it if needed.
- The **optimizer** allows you to configure the packages that you need.
    Afterwards, you can initialize it with the instance data and then solve the optimization problem.

## Installation & Usage

```cli
pip install optiframe
```

Take a look at the `examples` folder for examples on how to use Optiframe!

## License

This project is available under the terms of the [MIT license](LICENSE).
