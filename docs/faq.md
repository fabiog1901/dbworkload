# FAQ

🙋🏼 **I get this error message**

```text
error_type=ProgrammingError, msg=the query has 2 placeholders but 1 parameters were passed
```

➡️ _One of your functions uses a SQL query with 2 placeholders (`%s`) but in your `cur.execute()` you are not passing any argument.
Below is how you can replicate this_

```python
import psycopg

with psycopg.connect("postgres://...") as conn:
    with conn.cursor() as cur:
        cur.execute(
            "insert into t values (%s, %s)",
            (
                "just one item",
                # but it needs 2
            ),
        )
```
