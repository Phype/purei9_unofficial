Currently implemented functions
-------------------------------

|                  |    Local    |   Cloud v1  |   Cloud v2  |
| :---             |    :---:    |    :---:    |    :---:    |
| Get status       |      ✓      |      ✓      |      ✓      |
| Start robot      |      ✓      |      ✓      |      ✓      |
| Send home        |      ✓      |      ✓      |      ✓      |
| Stop  robot      |      ✓      |      ✓      |      ✓      |
| Pause robot      |✓<sup>1</sup>|      ✓      |      ✓      |
| Clean zone       |      –      |      ✓      |      ✓      |
| Change powermode |      ✓      |      ✓      |             |
| List wifis       |      ✓      |      –      |      –      |
| List maps/zones  |      –      |      ✓      |      ✓      |
| Map/zone images  |      –      |     (✓)     |             |
| Get history      |      –      |     (✓)     |             |

✓: works  
(✓): works, but needs refactoring for cross-API support  
–: impossible  
<sup>1</sup>: Pausing over local interfaces actually toggles between play/pause  
