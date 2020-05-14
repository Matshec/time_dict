# Time Dictionary
![Unittests](https://github.com/Matshec/time_dict/workflows/Unittests/badge.svg)

Now objects age too! - 
Automatically manage your objects based on age

### How to install
`> pip install timedict`

### Overview
This module implements self-updating structure that is able to handle updating and removing object based on age.
Objects added to this structure are assigned timestamp at insertion, then when age of object is exceeded optional
action function is called and object is removed from the structure.
### NOTE
When using this structure you must explicitly delete it due to thread locking either by
calling `destroy()` method or deleting it as `del d` or the interpreter will hang at exit

### Example Usage
```python
from time_dict import TimeDict
cache = TimeDict(action_time=2, poll_time=0.5)
key = '1'
cache[key] = 1
key in cache
del cache
```
---
### Main parameters are:
   
    action_time - which specifies age in second at which objects should be deleted - 
                time when actions should be performed and object will be deleted from structure
                
    poll_time - frequency in seconds of polling the objects for age timeout,
                experimentally should be around 1/4 of the action_time or less. 
                Please not that too frequent polling
                may negatively affect you application performance
                
    action  -   function that is called on object age timeout. 
                Signature is 'fn(key:Any, value:Any) -> None'
                 
    no_delete - do not delete objects when actions was called
       
       
Class **PARTIALLY**  implements dictionary interface, implementations allows for:
```python
d = TimeDict(action_time=2, poll_time=0.5)
insertion:
    d[key] = value
updating:
    NOTE: updating only changes the value, age remains unchanged
    d[key] = value
deletion:
      del d[key]
testing for membership:
    key in d
checking length:
    len(d)
```
All of the above method have optimistic time complexity of O(1) and pessimistic of O(n) due to thread locking
except for `del` which always is O(n)


 Rest of the dictionary interface is not implemented by design.
 
### Methods are:
`clear() → None`

Safely clear all data in the structure :raises Exception

`destroy() → None`

Destroys the structure, must be called to properly deinitialize it

`flush() → None`


Flush all the objects by calling the action function, 
does not remove objects Does not respect object age, 
calls action method on all objects :raises Exception if updated thread died
