## Linting

```
autoflake --remove-all-unused-imports --remove-unused-variables --ignore-init-module-imports -ir ciftools && isort . && black .
```