
## file_header 
1. pagesize           4bytes
2. keysize            4bytes
3. valuesize          4bytes
4. root_index         4bytes
5. first_free_page    4bytes 
6. first_left_leaf    4bytes
7. page_nums          4bytes


## page 
1. type  4bytes
2. first_record_pointer 4bytes
3. record_nums 4bytes
4. first_free_pointer 4 bytes
5. unassigned_space_pointer

## leaf_record (fixed length encoding) 
record length is 28
1. key  8 bytes
2. value 8 bytes (too) support long only right now
3. next 4 bytes

## internal_record (fixed length encoding) 
record length is 28
1. key  8 bytes
2. child 8 bytes (too) support long only right now
3. next 4 bytes