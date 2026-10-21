from aehf.judges.calibration import cohen_kappa

ground_truth = [True, True, False, True, False, True, True, False, True, True]
llm_judge_results = [True, True, False, True, False, True, False, False, False, True]

kappa = cohen_kappa(llm_judge_results, ground_truth)
print(kappa)