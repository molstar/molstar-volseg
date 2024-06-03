## tasks

### Lint

```
autoflake --remove-all-unused-imports --remove-unused-variables --ignore-init-module-imports -ir . && isort . && black .
```

TODO: add a makefile or something with this