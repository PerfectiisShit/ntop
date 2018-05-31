# ntop
An atop liked tool to display nginx access log

## Usage
<pre>python36 main.py --format main --path access_log</pre>

<pre>
  Total Requests  30699 Unique Visitors  106 Unique Files 2177 Referrers 0
  Valid Requests  30699 Init. Proc. Time 2s  Static Files 39   Log Size  4.84 MiB
  Failed Requests 0     Excl. IP Hits    0   Unique 404   5490 Bandwidth 134.26 MiB
  Log Source      access_log  


Requested Files (URLs)  

Hits      %h    Bandwidth  Method   Protocol  Data  

894    4.11%      9.66MiB  GET      HTTP/1.1  /emails/
228    1.05%     70.93KiB  GET      HTTP/1.0  /
195    0.90%      1.86MiB  GET      HTTP/2.0  /emails/

Static Requests  

Hits      %h    Bandwidth  Method   Protocol  Data  

195    0.90%     21.92MiB  GET      HTTP/1.1  /static/css/bootstrap.css
157    0.72%     43.44KiB  GET      HTTP/1.1  /static/css/style.css
114    0.52%      9.79MiB  GET      HTTP/1.1  /static/favicon.ico

Not Found URLs (404s)  

Hits      %h    Bandwidth  Method   Protocol  Data  

96     0.44%     21.84KiB  GET      HTTP/1.0  /q79w_38jg__.shtml
74     0.34%     16.84KiB  GET      HTTP/1.1  /console/login/LoginForm.jsp
73     0.34%     16.61KiB  GET      HTTP/1.1  /2014/users/6/shipping_addresses
</pre>