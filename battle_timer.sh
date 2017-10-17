if [ $# -gt 1 ]; then
  id=$1
  seconds=$2
  echo "sleeping $2 seconds, before:"
  echo "wget -O - http://elma.eartheart.se/ajax_battleh2h/end_battle?id=$id >/dev/null 2>&1"
  sleep $2
  wget -O - http://elma.eartheart.se/ajax_battleh2h/end_battle?id=$id >/dev/null 2>&1
fi
