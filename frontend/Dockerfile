FROM nginx:1.27-alpine

COPY docker/default.conf /etc/nginx/conf.d/default.conf
COPY docker/40-generate-config.sh /docker-entrypoint.d/40-generate-config.sh
RUN chmod +x /docker-entrypoint.d/40-generate-config.sh
COPY . /usr/share/nginx/html/
# Keep build helpers out of the web root.
RUN rm -rf /usr/share/nginx/html/docker
EXPOSE 80
