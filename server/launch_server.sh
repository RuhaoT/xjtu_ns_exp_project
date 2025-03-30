export WORKING_DIR=$(pwd)
export APACHE_ENVVARS=$WORKING_DIR/apache_config/envvars

# invoke apache2ctl
apache2ctl -k restart -f $WORKING_DIR/apache_config/apache2.conf