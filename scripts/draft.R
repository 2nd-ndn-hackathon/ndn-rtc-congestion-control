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

filename <- "output7_c1_2.csv"

data = read.table(paste("../results/day2/",filename, sep=""), header=T)

data$rtt <- data$rtt_prime_ms - data$Dgen_ms



g.rtt.prime <- ggplot(data, aes (x=rts_ms/1000, y=rtt_prime_ms)) +
  geom_line(size=0.8) + 
  xlab("Time [s]") +
  ylab("RTT [ms]") +
  ggtitle("RTT Prime")
  #facet_wrap(~ Node) 

# g.rtt_est <- ggplot(data, aes (x=rts_ms/1000, y=rtt_est_ms)) +
#   geom_line(size=0.8) + 
#   xlab("Time [s]") +
#   ylab("RTT [ms]") +
#   ggtitle("RTT Est")
# #facet_wrap(~ Node) 


g.rtt <- ggplot(data, aes (x=rts_ms/1000, y=rtt)) +
  geom_line(size=0.8) + 
  xlab("Time [s]") +
  ylab("Dgen [ms]") +
  ggtitle("RTT")
#facet_wrap(~ Node) 


g.dgen <- ggplot(data, aes (x=rts_ms/1000, y=Dgen_ms)) +
  geom_line(size=0.8) + 
  xlab("Time [s]") +
  ylab("Dgen [ms]") +
  ggtitle("Data Generation Delay")
#facet_wrap(~ Node) 


g.darr <- ggplot(data, aes (x=rts_ms/1000, y=Darr_ms)) +
  geom_line(size=0.8) + 
  xlab("Time [s]") +
  ylab("Dgen [ms]") +
  ggtitle("Data Inter-Arrival Delay")
#facet_wrap(~ Node) 



g.buf <- ggplot(data, aes (x=rts_ms/1000, y=buf_play_ms)) +
  geom_line(size=0.8) + 
  xlab("Time [s]") +
  ylab("Buffer size [ms]") +
  ggtitle("Playout Buffer")
#facet_wrap(~ Node) 


g.lambdad <- ggplot(data, aes (x=rts_ms/1000, y=lambda_d)) +
  geom_line(size=0.8) + 
  xlab("Time [s]") +
  ylab("Lambda [ms]") +
  ggtitle("Lambda (Cwnd)")
#facet_wrap(~ Node) 

pdf(paste("../graphs/",filename,".pdf", sep=""), useDingbats=T, width=12)
g.rtt
g.rtt.prime
g.dgen
g.darr
g.buf
g.lambdad
dev.off()
#embed_fonts("../graphs/rates.pdf")

summary(data$run)

