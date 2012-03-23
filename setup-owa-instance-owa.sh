#!/bin/bash

OWA_INSTALL_LOCATION=/opt/

pushd $OWA_INSTALL_LOCATION

wget "http://downloads.openwebanalytics.com/owa/owa_1_5_2.tar"
tar -xf owa_1_5_2.tar

chown -R apache:apache owa/

pushd owa

ls

popd
popd