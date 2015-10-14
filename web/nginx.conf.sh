cat << EOF
server {
  listen 80;

  location / {
    include uwsgi_params;
    uwsgi_pass $APP_PORT_3030_TCP_ADDR:$APP_PORT_3030_TCP_PORT;
  }
}
EOF
