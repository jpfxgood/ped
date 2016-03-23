import nntplib_ssl
import pprint

nn = nntplib_ssl.NNTP_SSL(host = "news.metacarta.com", user="jgoodwin", password="wapa2006")
print nn.help()
print nn.help()
#resp, count, first, last, name = nn.group("mc.sqa")
#print "count=",count,"first=",first,"last=",last, "name=",name, "resp=",resp
#newnews = nn.newnews("mc.sqa.auto","090722","000000")
#pprint.pprint(newnews)
#news_group = nn.group("mc.sqa")
#print news_group
#end = int(news_group[3])
#start = max(0,end-5)
#print start,end
#over = nn.xover(str(start),str(end))[1]
#pprint.pprint(over)
#for article in over:
#    pprint.pprint(nn.article(article[0]))
