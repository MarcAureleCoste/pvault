Generic single-database configuration.

# Commands to use alembic

### Auto generate migration

To generate a migration automatically run the following command:

```bash
alembic revision --autogenerate -m "Your message"
```

### Upgrade to the last migration

To upgrade the last migration simply run:

```bash
alembic upgrade head
```

### Downgrade to a specifique migration

To downgrade to a spechifique migration run:

```bash
alembic downgrade revision_id
```

### History

You can show the history of revisions and know the actual head using this command:

```bash
alembic history
```
