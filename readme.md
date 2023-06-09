[![Lifecycle:Experimental](https://img.shields.io/badge/Lifecycle-Experimental-339999)](<Redirect-URL>)

# Contents:

* [Overview](#overview)
* [Frontend Research](#frontend-research)
* [Run Streamlit App Locally](#run-streamlit-app---local)
* [Run Streamlit App Locally - Docker](#run-streamlit-app---local-with-docker)
* [Deploy Application using pipeline](#deploy-streamlit-app---using-pipeline)

# Overview

Currently in a research stage looking into how we can create a V1 frontend /
static view of the data that is getting generated by the snowpack analysis.

Current objective is fastest way to put up a very simple ui that makes the
snowpack analysis data easy to view.

# Frontend Research

In light of fastest way to PROD looked into the following tech options:

* NUXT - hightly popular framework based on vue is what motivated looking into
         this.  Poked away at it for an hour and didn't feel like was making
         progress

* Vue - Love this as an option is likely what I will come back to, however
        lack of experience with JS/TS and glueing up async communication with
        object storage, resulted in veering away from this option initially.

* Atri - New framework with a gui builder.  Looks like it doesn't necessarily
        save a lot of time.  Eventually worth revisiting but in its current
        state came to concusion it would be easier to build the gui, normally.

* streamlit - Looks very easy to use, super simple for building UI's.  Ended up
        building using this framework.  Got initial prototype up in a matter of
        hours... then got bogged down for days trying to figure out best way
        to sort out interactivity.

        Example:
            * when a satellite config changes, update the view to only show the
              selected satellite
            * when basin / watershed is swapped update the specific basin
              selector pulldown, and refresh the view with first basin/watershed
              in the list

        Got some of this sorted out but still has lots of bugs.  Already into
        this for more days then I should have so stopping and trying to figure
        out how to deploy what I have.

        Long term.. pivot away from streamlit.. super heavy framework, images
        are 700Megs.  😲.

        Thinking ultimate solution is to bite the bullet and figure out vue.

* dash - Another intermediate solution, advantage is its all python, build time
        should be shorter as a result of familiarity.  Looks similar to streamlit
        but lighter weight.  (approx 250Megs vs 700Megs).  Still pretty heavy,
        could be there are ways of trimming unused dependencies to shrink image
        size.

        Provides lower level functionality, hight degree of granularity than
        streamlit.  Looks like it should be easier to figure out the callbacks
        for component interactivity issue experienced with streamlit.


# Run Streamlit App - Local

Instructions on getting the streamlit application up and running using either
a virtualenv or Docker.

## Set environment variables

* OBJ_STORE_BUCKET - bucket with the snowpack data
* OBJ_STORE_SECRET - secret to bucket with the snowpack data
* OBJ_STORE_USER - user id for ...
* OBJ_STORE_HOST - host for the service... example someservice.obj.store.com


### Create virtualenv and install dependencies

``` bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run streamlit

`streamlit run src/main.py`

should produce output that tells you what the url is to the app. You can usually
test at http://localhost:8105

# Run Streamlit App - Local With Docker

## [Set environment Variables - link](#set-environment-variables)

### Build Image

`docker image build -t streamlit .`

### Run Image

`docker run --env-file .env -p 8501:8501 streamlit`

Haven't figured out the network issues yet enabling you to use the url output
by the actual application.  Instead just use localhost to view the app.  link
below also:

[http://localhost:8501](http://localhost:8501)

# Deploy Streamlit App - Using pipeline

A cicd pipeline has been setup for this repo.  A pull request to main will
trigger and image build and deployment of an ephemeral version of the app.

The pipeline will update the pr with a link to the deployed app url.

Once the url has been tested / verified that it works, and does what its
suppose to a merge/close of the pr will:
* Remove the ephemeral environment
* Deploy the application to a production namespace
