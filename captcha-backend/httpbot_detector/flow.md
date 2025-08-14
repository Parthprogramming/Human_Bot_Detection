#Current 

1) The backend should be retrieving the baseline behavior of the user and compare it with the incoming user behavior and to check the anomaly in the behavior , use the mahalanobis distance to detect the anomaly distance . 



4) Check if the user is authorized by giving the alert message from the backend and show it not on the frontend . 
or 
4) implement the redis ,then  Check if the user is authorized by giving the alert message from the backend and show it not on the frontend . 

1) Pseudo-inverse distance



-------------------------------------------IMPORTANT---------------------------------------------------------
1) Ensure all pages dont looose the behavior metrics calculated when page refreshed or reloaded
2) Behavior should be persistent , when navigating thorugh differet pages of the web . 



Frontend : 
1)  The Globalbehaviortracker , tracks the behavior of the user across the pages of the website globally .
The Globalbehaviortracker is main component to track the behavior of the user due to the it is consistent across all the pages .

Backend : 
1) frontend sends the request to analysis 