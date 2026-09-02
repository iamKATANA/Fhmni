from search_router import needs_search


tests = [
    "Chno howa Python?",
    "شرح ليا machine learning",
    "Chno kayn jdide f lmaghrib lyoma?",
    "Ch7al taman dyal dollar daba?",
    "Who won the latest match?"
]


for test in tests:

    print(
        f"{test} → {needs_search(test)}"
    )