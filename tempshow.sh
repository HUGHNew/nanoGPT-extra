#!/bin/bash

temps=$(nvidia-smi --query-gpu=temperature.gpu --format=csv|tail +2|xargs)

single_limit=80
filter=35

temp_sum=0
using_count=0
for temp in $temps;do
  if [ $temp -ge $filter ];then
    temp_sum=$(expr $temp_sum + $temp)
    using_count=$(expr $using_count + 1)
  fi
done

limit=$(expr $using_count \* $single_limit)
pid=$(pgrep torchrun)
echo count: $using_count $limit pid:$pid current:$temp_sum
if [ $temp_sum -gt $limit ];then
    echo $pid should be killed
fi
