#!/bin/bash
start="Dec 17, 2022"
format="%Y-%m-%d"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.46"

path="https://ftp.ncbi.nlm.nih.gov/pub/pmc/manuscript/xml/"
prefix="author_manuscript_xml.incr."
suffix=".tar.gz"

function get_incr_file {
  echo $path$prefix$1$suffix
}

[ ! -d logs ] && mkdir logs

wait_limit=8
endtime=$(date +%s)
datetime=$(date +"$format" -d "$start")

for ((incr=1; $(date -d $datetime +%s) < $endtime; incr++));do
  # ignore wget flooding
  if [ $(expr $incr % $wait_limit) -eq 0 ];then
  wget -c -U '$UA' $(get_incr_file $datetime) > logs/$datetime.log 2>&1
  else
  nohup sh -c "wget -c -U '$UA' $(get_incr_file $datetime) > logs/$datetime.log 2>&1" &
  fi
  datetime=$(date +"$format" --date "$start +$incr days")
done
