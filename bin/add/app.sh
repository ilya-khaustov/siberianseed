#!/bin/sh

# Creates an empty app.

echo "Creating app in $root";

cd $root/src;
read -p "Choose an app name: " appname
if [ -z $appname ];
  then
    echo "Empty name given, exit"; exit 0; fi
if [ -d $appname ];
  then
    echo "App $appname already exists";
  else
    mkdir "$appname";
    mkdir -p "$root/bin/$appname";
    mkdir -p "$root/share/$appname";
    echo "App $appname created successfully";
fi
