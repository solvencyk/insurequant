#!/bin/bash
# wait until free RAM >= 3 GB (max 10 min)
for i in $(seq 1 60); do
  f=$(powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,2)")
  echo "free_gb=$f"
  ok=$(powershell -NoProfile -Command "if ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB -ge 3) {'yes'} else {'no'}")
  if [ "$ok" = "yes" ]; then echo READY; exit 0; fi
  sleep 10
done
echo TIMEOUT
