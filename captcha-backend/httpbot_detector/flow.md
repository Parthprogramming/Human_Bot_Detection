1) for new user , User behaviorial metrics should be calculated after the user has been sign-up and the credentials stored in the "http:127.0.0.1:8000/user/store-baseline-behavior/" , "http:127.0.0.1:8000/user/signup/"and once the user has entered the main dasboard it should keep calculating the behaviorial metrics till the user has clicked on the log out and this will be treated as the baseline behavior .

2) When that same user sign-in , User behaviorial metrics should be calculated continously after the user has logged in and should be sent to the url : "http:127.0.0.1:8000/user/behavioral-analysis/" for continous detection of the authenticated user .

3) user behaviorial metrics should only calculated on the main dashboard page . 