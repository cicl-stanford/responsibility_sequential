library(brms)
library(tidyverse)
library(tidybayes)
library(broom)
library(broom.mixed)

options(dplyr.summarise.inform = F)

# Read the experiment data
file_path <- "../data/experiment1/counterfactual_sequential_exp1-trials.csv"
data <- read.csv(file_path)
# drop trial 0 (practice trial)
data <- data[data$trial != 0, ]

# separate the data into two subsets
# odd trials correspond to counterfactual successes and
# even trials correspond to counterfactual failures
data_odd <- data[data$trial %% 2 != 0,]
data_even <- data[data$trial %% 2 == 0,]

# sort by workerid and trial
data_odd <- data_odd[order(data_odd$workerid, data_odd$trial), ]
data_even <- data_even[order(data_even$workerid, data_even$trial), ]

# set diff to be the difference between the
# participant's human responsibility judgment
# in the respective odd and even trials (\Delta_H in the paper)
data_odd$diff <- data_odd$human - data_even$human


###### TEST 1 ######
# test whether counterfactuals have an
# effect on the human responsibility judgment
sink("analysis/files/results_bayes_test_counterfactual.txt")

counterfactual_model <- brm(diff ~ 1 + (1 | workerid) + (1 | trial),
                            data = data_odd,
                            seed = 42,
                            iter = 4000,
                            file = "analysis/model_cache/bayes_test_counterfactual")

summary(counterfactual_model)


###### TEST 2 ######
# test whether the effect of counterfactuals
# is stronger for wrong decisions than for right decisions
sink("analysis/files/results_bayes_test_decision_quality.txt")

# add a new column called decision that is 1 if the decision
# was wrong and 0 if decision was right
# twin trials with right decisions: 1 (2), 5 (6), 9 (10), 13 (14)
data_odd$decision <- ifelse(data_odd$trial %in% c(1, 5, 9, 13), 0, 1)

decision_model <- brm(diff ~ 1 + decision + (1 + decision | workerid) + (1 | trial),
                      data = data_odd,
                      seed = 42,
                      iter = 4000,
                      file = "analysis/model_cache/bayes_test_decision_quality")

summary(decision_model)