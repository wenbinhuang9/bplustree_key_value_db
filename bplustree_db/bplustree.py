from bisect import bisect_right
import os
from randomaccessfile import randomaccessfile
from bplustree_db import INTERNAL_NODE, LEAF_NODE, NEGATIVE_INFINITY

## the first worry, insert value into empty internal point

## support node split
## and a delete framework occurs
class internal_node:
    def __init__(self, page_idx):
        self.keys = []
        self.childs = []
        self.record_pos = None
        self.node_type = INTERNAL_NODE

        self.first_record_pointer = None
        self.record_nums = 0
        self.first_free_pointer = None
        self.page_idx = page_idx

        self.first_free_pointer_pos = None
        self.first_record_pointer_pos = None
        self.record_nums_pos = None

    def isempty(self):
        return self.record_nums == 0
    def get_record_pos(self, idx):
        if idx == -1:
            return self.first_record_pointer_pos
        ## -1 means the end of records
        if idx >= self.record_nums:
            return -1
        return self.record_pos[idx]

    def only_one_infinity(self):
        if self.record_nums == 1 and self.keys[0] == NEGATIVE_INFINITY:
            return True
        return False

class leaf_node:
    def __init__(self, page_idx):
        self.keys = None
        self.values = None
        self.record_pos = None
        self.first_record_pointer = None
        self.record_nums = 0
        self.first_free_pointer = None
        self.page_idx = page_idx

        self.node_type = LEAF_NODE

        self.prevpointer = None
        self.nextpointer = None

        self.first_free_pointer_pos = None
        self.first_record_pointer_pos = None
        self.record_nums_pos = None

    def isempty(self):
        return self.record_nums == 0

    def get_first_free_pointer_pos(self):
        return self.first_free_pointer_pos

    def get_record_pos(self, idx):
        if idx == -1:
            return self.first_record_pointer_pos
        ## -1 means the end of records
        if idx >= self.record_nums:
            return -1
        return self.record_pos[idx]

    def only_one_infinity(self):
        if self.record_nums == 1 and self.keys[0] == NEGATIVE_INFINITY:
            return True
        return False

## do those fixed length key and value and page size
class bplus_tree:
    def __init__(self):
        self.pagesize = 1024
        self.keysize = 8
        self.valuesize = 8
        self.root_page_idx = None
        self.first_free_page = None
        self.first_left_leaf = None
        self.page_nums = 0
        self.default_db_name = "plustree.db"
        self.recordsize = None
        self.file_head_size = None
        self.first_free_page_pos = None
        self.file = None
        self.root_page_idx_pos = None

        ## default by now
        self.tree_degree = 25

        self.page_nums_pos = None

    def get_min_child(self):
        return self.tree_degree - 1

    def get_max_child(self):
        return self.tree_degree * 2 - 1


    def open(self, path):
        if not os.path.exists(path + "/" + self.default_db_name):
            self._init_tree(path)
        else:
            self._init_read_bplustree_conf(path)

        return self

    def get(self, key):
        if self.root_page_idx == None or self.root_page_idx == -1:
            return None
        if self.root_page_idx == None or self.root_page_idx == -1:
            print("bug")
        root_node = self.read_node(self.root_page_idx)

        return self._get(key, root_node)
    def _get(self, key, node):
        if node.node_type == LEAF_NODE:
            return self.get_val_in_leaf(key, node)

        inserted_idx = bisect_right(node.keys, key, 0, node.record_nums) - 1
        child_page = node.childs[inserted_idx]
        child_node = self.read_node(child_page)
        return self._get(key, child_node)

    def get_val_in_leaf(self, key, leaf_node):
        idx = self.get_inserted_index(leaf_node, key)
        if idx >=0 and idx < leaf_node.record_nums and leaf_node.keys[idx] == key:
            return leaf_node.values[idx]

        return None

    def is_min_child(self, node):
        return  node.record_nums == self.get_min_child()

    ## TODO a delete bug here
    def delete(self, key):
        root = self.read_node(self.root_page_idx)

        self._delete(key, root, None)

    def _not_root_node(self, node):
        return node.page_idx != self.root_page_idx

    def is_root_node(self, node):
        return not self._not_root_node(node)

    def _delete(self, key, node, parent):
        if self.is_leaf(node):
            self._delete_leaf(key,node)
            if self.is_root_node(node) and node.isempty():
                self._update_root_index( -1)
        else:
            inserted_idx = self.get_inserted_index(node, key)
            child_idx = node.childs[inserted_idx]
            child = self.read_node(child_idx)

            if self.is_min_child(child) and self._not_root_node(child):  ## if parent is none, it means it is a root node
                self.borrow_or_merge(key, child, node, inserted_idx)

                ##update root page index
                if self.is_root_node(node) and (node.isempty() ):
                    self._update_root_index(child.page_idx)

                inserted_idx = self.get_inserted_index(node, key)
                child = self.read_node(node.childs[inserted_idx])


            self._delete(key, child, node)

    def _can_borrow(self, node):
        return node != None and node.record_nums >= self.get_min_child() + 1

    def borrow_or_merge(self, key, child, parent, idx):
        left_child_idx = parent.childs[idx - 1] if idx - 1 >= 0 else None
        right_child_idx = parent.childs[idx + 1] if idx + 1 < parent.record_nums else None
        left_child =self.read_node(left_child_idx) if left_child_idx != None else None
        right_child =self.read_node(right_child_idx) if right_child_idx != None else None

        if self._can_borrow(left_child):
            left_child_nums = left_child.record_nums
            borrow_key = left_child.keys[left_child_nums - 1]
            borrow_child = left_child.values[left_child_nums- 1] if self.is_leaf(left_child) else left_child.childs[left_child_nums - 1]
            left_child.record_nums -= 1

            child.keys.append(-1)
            if self.is_leaf(child):
                child.values.append(-1)
            else:
                child.childs.append(-1)
            child.record_nums += 1

            self._shift_right(child.keys, 0)
            if self.is_leaf(child):
                self._shift_right(child.values, 0)
            else:
                self._shift_right(child.childs, 0)
            self._insert_into_pos(child.keys, 0, borrow_key)
            if self.is_leaf(child):
                self._insert_into_pos(child.values, 0, borrow_child)
            else:
                self._insert_into_pos(child.childs, 0, borrow_child)

            self._insert_into_pos(parent.childs[idx].keys, idx, borrow_key)

            child.record_nums += 1

            self.writenode(left_child)
            self.writenode(child)
            self.writenode(parent)

        elif self._can_borrow(right_child):
            borrow_key = right_child.keys[0]
            borrow_child = right_child.values[0] if self.is_leaf(right_child) else right_child.childs[0]
            self._shift_left(right_child.keys, right_child.record_nums, 1)

            if self.is_leaf(right_child):
                self._shift_left(right_child.values, right_child.record_nums, 1)
            else:
                self._shift_left(right_child.childs, right_child.record_nums, 1)

            right_child.record_nums -= 1

            child.keys.append(-1)
            if self.is_leaf(child):
                child.values.append(-1)
            else:
                child.childs.append(-1)

            child.keys.append(-1)
            self._insert_into_pos(child.keys, child.record_nums, borrow_key)
            if self.is_leaf(child):
                child.values.append(-1)
                self._insert_into_pos(child.values, child.record_nums, borrow_child)
            else:
                child.childs.append(-1)
                self._insert_into_pos(child.childs, child.record_nums, borrow_child)
            child.record_nums += 1

            self._insert_into_pos(parent.keys, idx + 1, right_child.keys[0])

            self.writenode(right_child)
            self.writenode(child)
            self.writenode(parent)
        else:
            ## todo can't merge , just place the current node as the root? right?
            if left_child == None and right_child == None:
                self._update_root_index(child.page_idx)
                return
            if idx - 1 >=0:
                self._merge(parent, idx)
            else:
                self._merge(parent, idx + 1)

    def _insert_into_pos(self, arr, idx, val):
        arr[idx] = val

    def _shift_right(self, arr, record_nums, idx):
        for i in range(record_nums - 1, idx - 1, -1):
            arr[i + 1] = arr[i]

    def _shift_left(self, arr, record_nums, idx):
        for i in range(idx, record_nums):
            arr[i - 1] = arr[i]

    def _release_page_idx(self, page_idx):
        next_free_page = self.file.readint(self.first_free_page_pos)
        self.file.writeint(page_idx, self.first_free_page_pos)
        self.file.writeint(next_free_page, page_idx)

    ## todo here may has a bug
    def _merge(self, parent, idx):
        child = self.read_node( parent.childs[idx] )
        left_child = self.read_node( parent.childs[idx - 1] )

        self._append_node(left_child, child)
        self._shift_left(parent.keys, parent.record_nums, idx + 1)
        self._shift_left(parent.childs, parent.record_nums, idx + 1)
        parent.record_nums -= 1

        self._release_page_idx(child.page_idx)

        self.writenode(parent)
        self.writenode(left_child)

    ## append first node to second node
    def _append_node(self, first, sec):
        self._copy(first.keys, first.record_nums, sec.keys, sec.record_nums)
        if sec.node_type == INTERNAL_NODE:
            self._copy(first.childs, first.record_nums, sec.childs, sec.record_nums)
        elif sec.node_type == LEAF_NODE:
            ## leaf node
            self._copy(first.values, first.record_nums, sec.values, sec.record_nums)
        else:
            assert False

        first.record_nums += sec.record_nums

    def _copy(self, arr, arr_len, becopied_arr, becopied_arr_len):
        l = arr_len
        for i in range(becopied_arr_len):
            ## arr may not have enough slots
            if l >= len(arr):
                arr.append(becopied_arr[i])
            else:
                arr[l] = becopied_arr[i]
            l += 1

    def _delete_leaf(self, key, node):
        assert node.node_type == LEAF_NODE
        inserted_idx = bisect_right(node.keys, key, 0, node.record_nums)

        self._shift_left(node.keys, node.record_nums, inserted_idx)
        self._shift_left(node.values, node.record_nums, inserted_idx)

        node.record_nums -= 1

        self.writenode(node)

    def read_node(self, page_idx):
        return self.read_leaf_node(page_idx)

    def read_internal_node(self, page_idx):
        internal = internal_node(page_idx)
        offset = page_idx
        internal.type = self.file.readint(offset)
        offset += 4
        internal.first_record_pointer  = self.file.readint(offset)
        offset += 4
        internal.record_nums = self.file.readint(offset)

        record_offset = internal.first_record_pointer
        for i in range(internal.record_nums):
            internal.keys[i] = self.file.readlong(record_offset)
            record_offset += self.keysize
            internal.childs[i] = self.file.readlong(record_offset)
            record_offset += self.valuesize

            next_record_pos = self.file.readint(record_offset)
            record_offset = next_record_pos

        return internal

    def _update_page_nums(self):
        self.file.writeint(self.page_nums, self.page_nums_pos)

    def insert_to_internal(self, internal, key, child_page_idx):
        assert internal.record_nums <= self.get_max_child()

        inserted_idx = bisect_right(internal.keys, key, 0, internal.record_nums)
        ## adding another member
        internal.keys.append(-1)
        internal.childs.append(-1)
        for i in range(internal.record_nums - 1, inserted_idx - 1, -1):
            internal.keys[i + 1] = internal.keys[i]
            internal.childs[i + 1] = internal.childs[i]
        internal.keys[inserted_idx] = key
        internal.childs[inserted_idx] = child_page_idx

        internal.record_nums += 1
        self.writenode(internal)

    def insert_to_leaf(self, key, value, leafnode):
        inserted_idx = self.get_inserted_index(leafnode, key)

        assigned_record_pos = self.find_free_record_to_insert_leaf(leafnode, key, value)

        ## insert into the linkedlist here
        prev_pos = leafnode.get_record_pos(inserted_idx)
        next_pos = leafnode.get_record_pos(inserted_idx + 1)
        self.linked_to_next_key(prev_pos, assigned_record_pos)
        self.linked_to_next_key(assigned_record_pos, next_pos)

        leafnode.record_nums += 1
        self.file.writeint(leafnode.record_nums, leafnode.record_nums_pos)

    def linked_to_next_key(self, current_pos, next_pos):
        self.file.writeint(next_pos, current_pos + self.keysize + self.valuesize)

    def _get_leaf_record_size(self):
        return self.keysize + self.valuesize + 4

    def find_free_record_to_insert_internal(self, internal, key, value):
        free_head = internal.first_free_pointer
        ## adjust fisrt_free_pointer, pointing to next free space
        next_free = self.file.readint(free_head)

        ## get into the empty space, repoints to the empty space
        if next_free == -1:
            next_free = free_head + self._get_leaf_record_size()
            self.file.writeint(-1, next_free)

        internal.first_free_pointer = next_free

        self.file.writeint(next_free, internal.get_first_free_pointer_pos())
        assert internal.first_free_pointer == self.file.readint(internal.get_first_free_pointer_pos())
        ## write data into the current record space
        self.file.writelong(key, free_head)
        self.file.writelong(value, free_head + self.keysize)

        return free_head

    def find_free_record_to_insert_leaf(self, leaf, key, value):
        free_head = leaf.first_free_pointer
        ## adjust fisrt_free_pointer, pointing to next free space
        next_free = self.file.readint(free_head)

        ## get into the empty space, repoints to the empty space
        if next_free == -1:
            next_free = free_head + self._get_leaf_record_size()
            self.file.writeint(-1, next_free)

        leaf.first_free_pointer = next_free

        self.file.writeint(next_free, leaf.get_first_free_pointer_pos())
        assert leaf.first_free_pointer == self.file.readint(leaf.get_first_free_pointer_pos())
        ## write data into the current record space
        self.file.writelong(key, free_head)
        self.file.writelong(value, free_head + self.keysize)

        return free_head


    ## todo update page number
    ## get the biggest one index smaller than the current key
    def get_inserted_index(self, node, key):
        idx = bisect_right(node.keys, key, 0, node.record_nums)
        return idx - 1

    def _is_node_full(self, node):
        return node.record_nums == self.get_max_child()

    def _is_root_empty(self):
        return self.root_page_idx == None or self.root_page_idx == -1
    ## todo just using writing leaf with the whole node
    def insert(self, key, value):
        if self._is_root_empty():
            self.root_page_idx = self._init_root(key ,value)
        else:
            root = self.read_node(self.root_page_idx)
            if self._is_node_full(root):
                new_root = self._init_empty_internal_root(root.page_idx)
                self._update_root_index(new_root.page_idx)
                self.splitnode(root, new_root)
                root = new_root


            self.insert_non_full(key, value, root)

    def is_leaf(self, node):
        return node.node_type == LEAF_NODE

    def insert_non_full(self, key, value, node):
        if self.is_leaf(node):
            self.insert_to_leaf(key, value, node)
        else:
            page_idx = self.get_next_page_idx(node, key)
            child_node = self.read_node(page_idx)
            if self._is_node_full(child_node):
                self.splitnode(child_node, node)
                page_idx = self.get_next_page_idx(node, key)
                child_node = self.read_node(page_idx)
            self.insert_non_full(key, value, child_node)

    def get_next_page_idx(self, node, key):
        insertedidx = self.get_inserted_index(node, key)

        return node.childs[insertedidx]



    def writenode(self, node):
        return self.writeleaf(node)
    def splitnode(self, node, parent):
        right_half_node = self.gen_right_half_node(node)

        self.writenode(right_half_node)
        self.writenode(node)
        self.increase_page_nums()

        key = right_half_node.keys[0]
        new_child = right_half_node.page_idx

        self.insert_to_internal(parent, key, new_child)



    def gen_right_half_node(self, node):
        return self.gen_right_half_internal_node(node) if node.node_type == INTERNAL_NODE else self.gen_right_half_leaf_node(node)

    def gen_right_half_internal_node(self, node):
        right_node = self.create_node(node.node_type)
        mid = node.record_nums / 2

        right_node.record_nums = node.record_nums - mid
        right_node.keys  = [-1] * right_node.record_nums
        right_node.childs = [-1] *right_node.record_nums

        l = 0
        for i in range(mid, node.record_nums):
            right_node.keys[l] = node.keys[i]
            right_node.childs[l] = node.childs[i]
            l += 1

        node.record_nums = mid
        return right_node

    def gen_right_half_leaf_node(self, node):
        right_node = self.create_node(node.node_type)

        mid = node.record_nums/2
        right_node.record_nums = node.record_nums - mid
        right_node.keys  = [-1] * right_node.record_nums
        right_node.values = [-1] *right_node.record_nums
        l = 0
        for i in range(mid, node.record_nums):
            right_node.keys[l] = node.keys[i]
            right_node.values[l] = node.values[i]
            l += 1

        node.record_nums = mid
        return right_node


    def create_node(self, node_type):
        page_idx = self.get_available_page_index()
        return internal_node(page_idx) if node_type == INTERNAL_NODE else leaf_node(page_idx)

    def get_first_free_page_offset(self):
        return self.first_free_page_pos

    ## todo what if page is full if pagenum reduce, it has a big bug here
    def get_available_page_index(self):
        if self.first_free_page == None:
            ## get available_page from the ending of file
            page_idx = self.file_head_size + self.page_nums * self.pagesize
            return page_idx

        page_idx = self.first_free_page

        next_free_page = self.file.readint(self.first_free_page)
        self.file.writeint(next_free_page, self.get_first_free_page_offset())
        self.first_free_page = next_free_page

        return page_idx

    def create_new_leaf_node(self, page_idx, key, value):
        leaf = leaf_node(page_idx)
        leaf.keys = [NEGATIVE_INFINITY]
        leaf.values = [NEGATIVE_INFINITY]
        leaf.keys.append(key)
        leaf.values.append(value)
        leaf.record_nums += 2

        return leaf


    def writeleaf(self, leafnode):
        offset = leafnode.page_idx

        self.file.writeint(leafnode.node_type, offset)

        offset += 4
        first_record_pointer_pos = offset
        self.file.writeint(leafnode.first_record_pointer, offset)
        offset += 4
        self.file.writeint(leafnode.record_nums, offset)
        offset += 4
        first_free_pointer_pos = offset
        self.file.writeint(leafnode.first_free_pointer, offset)
        offset += 4
        for i in range(leafnode.record_nums):
            if i == 0:
                ## recording the first record pointer
                self.file.writeint(offset,first_record_pointer_pos)
            self.file.writelong(leafnode.keys[i], offset)
            offset += self.keysize
            self.write_values_or_childs(leafnode, i, offset)
            ## todo warning if valuesize, it will influene the inernal writing here
            offset += self.valuesize
            next_node_offset = -1 if i == leafnode.record_nums - 1 else offset + 4
            self.file.writeint(next_node_offset, offset)
            offset += 4

        ## record the empty space
        page_empty_space_pos = offset
        self.file.writeint(page_empty_space_pos, first_free_pointer_pos)
        ## using flag -1 to indicate here is a empty space
        self.file.writeint(-1, page_empty_space_pos )

        return True

    def write_values_or_childs(self, node, i, offset):
        if node.node_type == LEAF_NODE:
            self.file.writelong(node.values[i], offset)
        else:
            self.file.writelong(node.childs[i], offset)


    def read_leaf_node(self, page_idx):
        offset = page_idx
        node_type = self.file.readint(offset)

        leaf = leaf_node(page_idx) if node_type == LEAF_NODE else internal_node(page_idx)
        leaf.node_type = self.file.readint(offset)
        offset += 4
        leaf.first_record_pointer_pos = offset
        leaf.first_record_pointer  = self.file.readint(offset)
        offset += 4

        leaf.record_nums_pos = offset
        leaf.record_nums = self.file.readint(offset)
        offset += 4

        leaf.first_free_pointer_pos = offset
        leaf.first_free_pointer =self.file.readint(offset)
        offset += 4

        record_offset = leaf.first_record_pointer
        leaf.keys = [-1] * leaf.record_nums
        if leaf.node_type == LEAF_NODE:
            leaf.values = [-1] * leaf.record_nums
        else:
            leaf.childs = [-1] *leaf.record_nums
        leaf.record_pos = [-1] * leaf.record_nums
        for i in range(leaf.record_nums):
            leaf.record_pos[i] = record_offset

            leaf.keys[i] = self.file.readlong(record_offset)
            record_offset += self.keysize

            self._read_values_or_childs(leaf, i, record_offset)
            ## todo warning here, if valuesize changed, may influence the read of internal node
            record_offset += self.valuesize

            next_record_pos = self.file.readint(record_offset)
            ## pointing to next value
            record_offset = next_record_pos

        return leaf
    def _read_values_or_childs(self, node, i, offset):
        if node.node_type == LEAF_NODE:
            node.values[i] = self.file.readlong(offset)
        else:
            node.childs[i] = self.file.readlong(offset)


    def _update_root_index(self, new_root_index):
        self.file.writeint(new_root_index, self.root_page_idx_pos)
        self.root_page_idx = new_root_index

    def increase_page_nums(self):
        self.page_nums += 1
        self._update_page_nums()

    def _init_empty_internal_root(self, page_idx):
        page_index = self.get_available_page_index()

        root = internal_node(page_index)
        root.keys.append(NEGATIVE_INFINITY)
        root.childs.append(page_idx)
        root.record_nums += 1
        self.writenode(root)
        self.increase_page_nums()

        root = self.read_node(root.page_idx)
        return root

    def _init_root(self, key, value):
        page_index = self.get_available_page_index()

        leaf = self.create_new_leaf_node(page_index, key, value)

        self.writeleaf(leaf)
        self._update_root_index(page_index)

        self.increase_page_nums()
        return page_index


    def close(self):
        pass


    def _init_tree(self, path):
        self.file = randomaccessfile(path + "/" + self.default_db_name, "w+")
        offset = 0
        self.file.writeint(self.pagesize)
        offset += 4
        self.file.writeint(self.keysize)
        offset += 4
        self.file.writeint(self.valuesize)
        offset += 4
        self.root_page_idx_pos = offset
        self.file.writeint(self.root_page_idx)
        offset += 4

        self.first_free_page_pos = offset
        self.file.writeint(self.first_free_page)
        offset += 4

        self.file.writeint(self.first_left_leaf)
        offset += 4

        self.page_nums_pos = offset
        self.file.writeint(self.page_nums, offset)
        offset += 4

        self.recordsize =self.keysize + self.valuesize
        self.file_head_size = offset



    def _init_read_bplustree_conf(self, path):
        self.file = randomaccessfile(path + "/" + self.default_db_name)

        offset = 0
        self.pagesize = self.file.readint(offset)
        offset += 4
        self.keysize = self.file.readint(offset)
        offset += 4
        self.valuesize = self.file.readint(offset)
        offset += 4
        self.root_page_idx_pos = offset
        self.root_page_idx =self.file.readint(offset)
        offset += 4
        self.first_free_page = self.file.readint(offset)
        offset += 4
        self.first_left_leaf = self.file.readint(offset)
        offset += 4
        self.page_nums = self.file.readint(offset)
        offset += 4
        self.file_head_size = offset

