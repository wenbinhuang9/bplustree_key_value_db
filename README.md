# bplustree_key_value_db
An in-disk b+ tree implementation

1. supporting get, insert ,delete, and range query.
2. with full unit tests

# interface 
```
tree = bplus_tree()
tree.open("./")
tree.insert(99, 999)
tree.get(99)
tree.delete(99)

```
