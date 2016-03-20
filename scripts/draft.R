library(ggplot2)
library(doBy)
library(plyr)
library(gridExtra)
library(reshape2)

setwd("/home/klaus/ccn/ndn-rtc-cc/scripts")


# theme_set(theme_bw(base_size = 12, base_family = "CM Sans"))
theme_set(theme_bw() + theme( strip.background=element_blank(), legend.key = element_rect(color="white"), panel.background=element_blank(), 
                              panel.border=element_blank(), axis.line = element_line(size=0.3)))

# Read in data
data = read.table("../results/run3/output3.csv", header=T)

summary(data)



g.rtt <- ggplot(data, aes (x=rts, y=rtt_prime)) +
  geom_line(size=0.8) + 
  ylab("RTT [ms]") +
  ggtitle("RTT")
  #facet_wrap(~ Node) 

g.rtt_est <- ggplot(data, aes (x=rts, y=rtt_est)) +
  geom_line(size=0.8) + 
  ylab("RTT [ms]") +
  ggtitle("RTT Est")
#facet_wrap(~ Node) 


g.dgen <- ggplot(data, aes (x=rts, y=Dgen)) +
  geom_line(size=0.8) + 
  ylab("Dgen [ms]") +
  ggtitle("Data Generation Delay")
#facet_wrap(~ Node) 


g.buf <- ggplot(data, aes (x=rts, y=buf_play)) +
  geom_line(size=0.8) + 
  ylab("Buffer size [ms]") +
  ggtitle("Playout Buffer")
#facet_wrap(~ Node) 



g.rtt
g.rtt_est

g.dgen


pdf("../graphs/draft.pdf", useDingbats=T, width=12)
g.rtt
g.rtt_est
g.dgen
g.buf
dev.off()
#embed_fonts("../graphs/rates.pdf")

