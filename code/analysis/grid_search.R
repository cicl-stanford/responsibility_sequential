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
    mutate(id = factor(id))

prob_data = read_csv('analysis/files/simulation_results.csv',
                    show_col_types = F)

all_data = resp_data %>%
  left_join(prob_data,
            by = 'trial',
            relationship = 'many-to-many') 

# add an indicator column called ai_drove that is 1 if ai_count > 0 and 0 otherwise
all_data <- all_data %>%
    mutate(ai_drove = ifelse(ai_count > 0, 1, 0))

# get all unique values of tau_scaler and theta_scaler
unique_pairs = all_data %>%
  select(tau_scaler, theta_scaler) %>%
  unique()

model_results <- list()

# iterate over all unique pairs of tau_scaler and theta_scaler
# for each pair, fit a model with the data from that pair
for (i in 1:nrow(unique_pairs)) {
    
    # print progress
    print(paste0("Fitting model ", i, " of ", nrow(unique_pairs)))
    
    current_pair <- unique_pairs[i, ]
    all_data_subset <- all_data %>%
        filter(tau_scaler == current_pair$tau_scaler &
            theta_scaler == current_pair$theta_scaler)

    # fit the human responsibility model
    model_human <- brm(
        formula = human ~ 1 + prob_succ_other_decision*prob_other_decision + (1 | id),
        data = all_data_subset,
        iter = 4000,
        seed = 42,
        file = paste0("analysis/model_cache/gridsearch_human_model_tau:", current_pair$tau_scaler, "_theta:", current_pair$theta_scaler, ".rds")
    )

    # add human responsibility predictions (and their complement) to the rest of the data
    all_data_subset <- all_data_subset %>%
    # cap predictions between 0 and 100
        mutate(cf_full_human = pmin(100, pmax(0, fitted(model_human)[, 1])),
               cf_full_human_complement = 100 - pmin(100, pmax(0, fitted(model_human)[, 1])))

    # fit the AI responsibility model
    model_ai <- brm(
        formula = ai ~ 1 + ai_drove:prob_succ_no_ai + cf_full_human_complement + (1 | id),
        data = all_data_subset,
        iter = 4000,
        seed = 42,
        file = paste0("analysis/model_cache/gridsearch_ai_model_tau:", current_pair$tau_scaler, "_theta:", current_pair$theta_scaler, ".rds")
    )

    # compute the correlation and RMSE between the model predictions and the data and store it in a list
    model_results[[i]] <- list(
        tau_scaler = current_pair$tau_scaler,
        theta_scaler = current_pair$theta_scaler,
        human_rmse = sqrt(mean((all_data_subset$human - pmin(100, pmax(0, fitted(model_human)[, 1])))^2)),
        ai_rmse = sqrt(mean((all_data_subset$ai - pmin(100, pmax(0, fitted(model_human)[, 1])))^2))
    )
}

sink("analysis/files/gridsearch_summary.txt")

# for each pair of tau_scaler and theta_scaler, print the RMSE of the human model and the AI model
for (i in 1:length(model_results)) {
    print(paste0("tau_scaler: ", model_results[[i]]$tau_scaler, ", theta_scaler: ", model_results[[i]]$theta_scaler))
    print(paste0("Human RMSE: ", model_results[[i]]$human_rmse, ", AI RMSE: ", model_results[[i]]$ai_rmse))
}
print("")

# find the model with the lowest human RMSE
min_human_rmse <- min(sapply(model_results, function(x) x$human_rmse))
min_human_model <- model_results[[which.min(sapply(model_results, function(x) x$human_rmse))]]

# print its RMSE and the corresponding tau_scaler and theta_scaler
print(paste0("Model with lowest human RMSE: tau_scaler: ", min_human_model$tau_scaler, ", theta_scaler: ", min_human_model$theta_scaler))
print(paste0("Human RMSE: ", min_human_rmse))