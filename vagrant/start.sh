#!/bin/sh

VAGRANT_DEFAULT_PROVIDER=virtualbox

vagrant init hashicorp/bionic64
vagrant up
vagrant provision
vagrant ssh
