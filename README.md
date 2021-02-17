# radar-test-plots
Plotting scripts used to visualize test data from the SuperDARN site equipment. Data to be plotted includes VSWRs, phase paths, sky noise, antenna coupling

# Tutorial

## Plotting VSWR

This uses the script `plot_vswrs.py` to plot VSWR data gathered from the R&S ZVH4.

Steps:

- Create a json file (example: 'vswr-files.json') with the following entries (this is an example) and place in a directory where you would like to have the VSWR plot (example: /Sync/Sites/Saskatoon/Trips/2021/20210127/vswr_main/DataAnalysis/). Note that the entries for each antenna ("M0", "I0", "I1", etc...) should correspond to the name of a single csv file like 'sas-vswr-full0.csv'.

    ```json
    {
        "M0" : "sas-vswr-full0.csv",
        "M1" : "sas-vswr-full1.csv",
        "M2" : "sas-vswr-full2.csv",
        "M3" : "sas-vswr-full3.csv",
        "M4" : "sas-vswr-full4.csv",
        "M5" : "sas-vswr-full5.csv",
        "M6" : "sas-vswr-full6.csv",
        "M7" : "sas-vswr-full7.csv",
        "M8" : "sas-vswr-full8.csv",
        "M9" : "sas-vswr-full9.csv",
        "M10" : "sas-vswr-full10.csv",
        "M11" : "sas-vswr-full11.csv",
        "M12" : "sas-vswr-full12.csv",
        "M13" : "sas-vswr-full13.csv",
        "M14" : "sas-vswr-full14.csv",
        "M15" : "sas-vswr-full15.csv",
        "I0"  : "sas-vswr-full16.csv",
        "I1"  : "sas-vswr-full17.csv",
        "I2"  : "sas-vswr-full18.csv",
        "I3"  : "sas-vswr-full19.csv"
    }
    ```

- Place your converted csv files together in a directory (example: /Sync/Sites/Saskatoon/Trips/2021/20211027/vswr_main/)
- Run the vswr plotting script like so:

    ```bash
    python3 ./plot_vswrs.py Saskatoon /Sync/Sites/Saskatoon/Trips/2021/20210127/vswr_main/ /Sync/Sites/Saskatoon/Trips/2021/20210127/vswr_main/DataAnalysis/ vswr-files.json
    ```

- Now view your plot in the directory with the vswr-files.json file.

