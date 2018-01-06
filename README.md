# lsreader
localStorage Reader for python 3 (tested with 3.6+)

## Examples
```python
import lsreader
for process in lsreader.search_processes(lambda fp, exe: exe == 'MyElectronApp'):
    storage = lsreader.find_local_storage(process)
    if storage:
        print (lsreader.LocalStorage('mystoragedomain', storage, proto='http')['token'].decode('utf-8'))
```
