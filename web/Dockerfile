FROM nginx

WORKDIR /opt/web
COPY nginx.conf.sh ./

CMD bash nginx.conf.sh > /etc/nginx/conf.d/default.conf && nginx -g "daemon off;"
