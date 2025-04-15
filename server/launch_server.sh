export WORKING_DIR=/home/ubuntu/xjtu_ns_exp_project/server/
export APACHE_ENVVARS=/home/ubuntu/xjtu_ns_exp_project/server/apache_config/envvars

# invoke apache2ctl
apache2ctl -k restart -f /home/ubuntu/xjtu_ns_exp_project/server/apache_config/apache2.conf