library(brms)
library(tidyverse)
library(tidybayes)
library(broom)
library(broom.mixed)

# read participants' data and simulation results 
resp_data = read_csv('../data/experiment1/counterfactual_sequential_exp1-trials.csv',
                    show_col_types = F) %>%
    rename(id = workerid) %>%
    drop_na(trial) %>%
    filter(trial != 0) %>%
    mutate(id = factor(id),
           num_id = as.numeric(id))

prob_data = read_csv('analysis/files/simulation_results.csv',
                    show_col_types = F)

all_data = resp_data %>%
  left_join(prob_data,
            by = 'trial',
            relationship = 'many-to-many')

# add an indicator column called ai_drove that is 1 if ai_count > 0 and 0 otherwise
all_data <- all_data %>%
    mutate(ai_drove = ifelse(ai_count > 0, 1, 0))

# add a column num_of_obstacles to use as a proxy for each trial's difficulty
# there are 6 obstacles in trials 1,2,13,14
# 5 in trials 5,6
# 4 in trials 3,4,7,8,9,10
# 3 in trials 11,12,15,16
all_data <- all_data %>%
    mutate(num_of_obstacles = ifelse(trial %in% c(1, 2, 13, 14), 6,
                                     ifelse(trial %in% c(5, 6), 5,
                                            ifelse(trial %in% c(3, 4, 7, 8, 9, 10), 4,
                                                   ifelse(trial %in% c(11, 12, 15, 16), 3, 0)))))

# select best tau and theta based on the results of the grid search
best_tau = 2
best_theta = 8

all_data_subset <- all_data %>%
    filter(tau_scaler == best_tau &
             theta_scaler == best_theta)

# add a column with the multiplicative effect of counterfactual expectancy and counterfactual probability of success
all_data_subset <- all_data_subset %>%
    mutate(mult_effect = prob_succ_other_decision * prob_other_decision)
# scale the 3 columns to be between 0 and 1
all_data_subset <- all_data_subset %>%
    mutate(prob_succ_other_decision = (prob_succ_no_ai - min(prob_succ_no_ai)) / (max(prob_succ_no_ai) - min(prob_succ_no_ai)),
           prob_other_decision = (prob_other_decision - min(prob_other_decision)) / (max(prob_other_decision) - min(prob_other_decision)),
           mult_effect = (mult_effect - min(mult_effect)) / (max(mult_effect) - min(mult_effect)))

# fit the human responsibility model
model_human <- brm(
    formula = human ~ 1 + prob_succ_other_decision + prob_other_decision + mult_effect + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/cf_full_human_tau:", best_tau, "_theta:", best_theta, ".rds")
)

# save the coefficients of the human responsibility model
sink("analysis/files/results_human_model_coefficients.txt")
summary(model_human)

# add human responsibility predictions (and their complement) to the rest of the data
    all_data_subset <- all_data_subset %>%
    # cap predictions between 0 and 100
        mutate(cf_full_human = pmin(100, pmax(0, fitted(model_human)[, 1])),
               cf_full_human_complement = 100 - pmin(100, pmax(0, fitted(model_human)[, 1])))


# fit the human responsibility model without the multiplicative term
model_human_add <- brm(
    formula = human ~ 1 + prob_succ_other_decision + prob_other_decision + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/cf_full_human_add_tau:", best_tau, "_theta:", best_theta, ".rds")
)

# add predictions to the rest of the data
all_data_subset <- all_data_subset %>%
    # cap predictions between 0 and 100
    mutate(cf_full_human_add = pmin(100, pmax(0, fitted(model_human_add)[, 1])))

# fit the AI responsibility model
model_ai <- brm(
    formula = ai ~ 1 + ai_drove:prob_succ_no_ai + cf_full_human_complement + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/cf_full_ai_tau:", best_tau, "_theta:", best_theta, ".rds")
)

# add predictions to the rest of the data
all_data_subset <- all_data_subset %>%
    mutate(cf_full_ai = pmin(100, pmax(0, fitted(model_ai)[, 1])))

# fit heuristic (actual contribution) models
heur_human = brm(
    formula = human ~ 1 + human_count + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/heur_human.rds")
)

heur_ai = brm(
    formula = ai ~ 1 + ai_count + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/heur_ai.rds")
)

# add predictions to the rest of the data
all_data_subset <- all_data_subset %>%
    mutate(heur_human = pmin(100, pmax(0, fitted(heur_human)[, 1])),
           heur_ai = pmin(100, pmax(0, fitted(heur_ai)[, 1])))

# fit advanced heuristic models (actual contribution + difficulty)
adv_heur_human = brm(
    formula = human ~ 1 + human_count + num_of_obstacles + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/adv_heur_human.rds")
)

adv_heur_ai = brm(
    formula = ai ~ 1 + ai_count + num_of_obstacles + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/adv_heur_ai.rds")
)

# add predictions to the rest of the data
all_data_subset <- all_data_subset %>%
    mutate(adv_heur_human = pmin(100, pmax(0, fitted(adv_heur_human)[, 1])),
           adv_heur_ai = pmin(100, pmax(0, fitted(adv_heur_ai)[, 1])))

# save the predictions of all trained models for each trial
trial_means <- all_data_subset %>%
    group_by(trial) %>%
    summarize(cf_full_human = mean(cf_full_human),
              cf_full_human_add = mean(cf_full_human_add),
              cf_full_ai = mean(cf_full_ai),
              heur_human = mean(heur_human),
              heur_ai = mean(heur_ai),
              adv_heur_human = mean(adv_heur_human),
              adv_heur_ai = mean(adv_heur_ai))

write_csv(trial_means, 'analysis/files/trial_means.csv')



#######################################################
# CROSS VALIDATION (how well does each model perform) #
#######################################################   
library(loo)
library(modelr)


# fit model that relies only on counterfactual expectancy
expectancy <- brm(
    formula = human ~ 1 + prob_other_decision + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/expectancy_tau:", best_tau, "_theta:", best_theta, ".rds")
)

# fit model that relies only on counterfactual probability of success
counterfactual <- brm(
    formula = human ~ 1 + prob_succ_other_decision + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/counterfactual_tau:", best_tau, "_theta:", best_theta, ".rds")
)

# fit model that relies only on their multiplicative effect
joint <- brm(
    formula = human ~ 1 + mult_effect + (1 | id),
    data = all_data_subset,
    iter = 4000,
    seed = 42,
    file = paste0("analysis/model_cache/joint_tau:", best_tau, "_theta:", best_theta, ".rds")
)


model_human = add_criterion(
  model_human,
  criterion = "loo",
  reloo = T,
  file = paste0("analysis/model_cache/cf_full_human_tau:", best_tau, "_theta:", best_theta, ".rds"))

model_human_add = add_criterion(
    model_human_add,
    criterion = "loo",
    reloo = T,
    file = paste0("analysis/model_cache/cf_full_human_add_tau:", best_tau, "_theta:", best_theta, ".rds"))

expectancy = add_criterion(
    expectancy,
    criterion = "loo",
    reloo = T,
    file = paste0("analysis/model_cache/expectancy_tau:", best_tau, "_theta:", best_theta, ".rds"))

counterfactual = add_criterion(
    counterfactual,
    criterion = "loo",
    reloo = T,
    file = paste0("analysis/model_cache/counterfactual_tau:", best_tau, "_theta:", best_theta, ".rds"))

joint = add_criterion(
    joint,
    criterion = "loo",
    reloo = T,
    file = paste0("analysis/model_cache/joint_tau:", best_tau, "_theta:", best_theta, ".rds"))

heur_human = add_criterion(
    heur_human,
    criterion = "loo",
    reloo = T,
    file = paste0("analysis/model_cache/heur_human.rds"))

sink("analysis/files/results_model_comparison.txt")

loo_compare(model_human,
            model_human_add,
            expectancy,
            counterfactual,
            joint,
            heur_human)

##################################################################
# N-BEST (which model best captures each individual participant) #
##################################################################

model_human_individual = brm(
  formula = human ~ 1 + prob_succ_other_decision + prob_other_decision + mult_effect,
  data = all_data_subset %>% 
    filter(num_id == 1),
  seed = 42,
  save_pars = save_pars(all = T),
  file = paste0("analysis/model_cache/cf_full_human_individual_tau:", best_tau, "_theta:", best_theta, ".rds"))

model_human_add_individual = brm(
  formula = human ~ 1 + prob_succ_other_decision + prob_other_decision,
  data = all_data_subset %>% 
    filter(num_id == 1),
  seed = 42,
  save_pars = save_pars(all = T),
  file = paste0("analysis/model_cache/cf_full_human_add_individual_tau:", best_tau, "_theta:", best_theta, ".rds"))

expectancy_individual = brm(
  formula = human ~ 1 + prob_other_decision,
  data = all_data_subset %>% 
    filter(num_id == 1),
  seed = 42,
  save_pars = save_pars(all = T),
  file = paste0("analysis/model_cache/expectancy_individual_tau:", best_tau, "_theta:", best_theta, ".rds"))

counterfactual_individual = brm(
    formula = human ~ 1 + prob_succ_other_decision,
    data = all_data_subset %>% 
        filter(num_id == 1),
    seed = 42,
    save_pars = save_pars(all = T),
    file = paste0("analysis/model_cache/counterfactual_individual_tau:", best_tau, "_theta:", best_theta, ".rds"))

joint_individual = brm(
    formula = human ~ 1 + mult_effect,
    data = all_data_subset %>% 
        filter(num_id == 1),
    seed = 42,
    save_pars = save_pars(all = T),
    file = paste0("analysis/model_cache/joint_individual_tau:", best_tau, "_theta:", best_theta, ".rds"))

heur_human_individual = brm(
    formula = human ~ 1 + human_count,
    data = all_data_subset %>% 
        filter(num_id == 1),
    seed = 42,
    save_pars = save_pars(all = T),
    file = paste0("analysis/model_cache/heur_human_individual.rds"))

# update model fits for each participant 
individual_fits = all_data_subset %>% 
  group_by(num_id) %>% 
  nest() %>% 
  ungroup() %>% 
  mutate(
         fit_model = map(.x = data,
                            .f = ~ update(model_human_individual,
                                          newdata = .x,
                                          seed = 42)),
         fit_model_add = map(.x = data,
                            .f = ~ update(model_human_add_individual,
                                          newdata = .x,
                                          seed = 42)),
         fit_expectancy = map(.x = data,
                            .f = ~ update(expectancy_individual,
                                          newdata = .x,
                                          seed = 42)),
         fit_counterfactual = map(.x = data,
                            .f = ~ update(counterfactual_individual,
                                          newdata = .x,
                                          seed = 42)),
         fit_joint = map(.x = data,
                               .f = ~ update(joint_individual,
                                             newdata = .x,
                                             seed = 42)),
         fit_heur = map(.x = data,
                            .f = ~ update(heur_human_individual,
                                          newdata = .x,
                                          seed = 42))) %>%
  mutate(fit_model = map(.x = fit_model,
                            .f = ~ add_criterion(.x, criterion = "loo",
                                                 moment_match = T)),
         fit_model_add = map(.x = fit_model_add,
                            .f = ~ add_criterion(.x, criterion = "loo",
                                                 moment_match = T)),
         fit_expectancy = map(.x = fit_expectancy,
                            .f = ~ add_criterion(.x, criterion = "loo",
                                                 moment_match = T)),
         fit_counterfactual = map(.x = fit_counterfactual,
                            .f = ~ add_criterion(.x, criterion = "loo",
                                                 moment_match = T)),
         fit_joint = map(.x = fit_joint,
                               .f = ~ add_criterion(.x, criterion = "loo",
                                                 moment_match = T)),
         fit_heur = map(.x = fit_heur,
                            .f = ~ add_criterion(.x, criterion = "loo",
                                                 moment_match = T)),
         model_comparison = pmap(.l = list(model = fit_model,
                                           model_add = fit_model_add,
                                           expectancy = fit_expectancy,
                                           counterfactual = fit_counterfactual,
                                           joint = fit_joint,
                                           heur = fit_heur),
                                 .f = ~ loo_compare(..1, ..2, ..3, ..4, ..5, ..6)),
         best_model = map_chr(.x = model_comparison,
                              .f = ~ rownames(.) %>% 
                                .[1]),
         best_model = factor(best_model,
                             levels = c("..1", "..2", "..3", "..4", "..5", "..6"),
                             labels = c("model",
                                        "model_add",
                                        "expectancy",
                                        "counterfactual",
                                        "joint",
                                        "heur")))

save(list = c("individual_fits"),
     file = 'analysis/model_cache/individual_fits.RData')

load(file = 'analysis/model_cache/individual_fits.RData')

individual_fits %>% 
  count(best_model) %>%
  arrange(desc(n))

data_with_best_model = all_data_subset %>%
  inner_join(individual_fits, by = "num_id")