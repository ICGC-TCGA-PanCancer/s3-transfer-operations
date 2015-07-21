#!/bin/bash
docker run -h master -it -v /var/run/docker.sock:/var/run/docker.sock  \
           -v /home/ubuntu/.gnos:/home/ubuntu/.gnos -v /datastore:/datastore \
           -v /workflows:/workflows -v $1:/workflow.ini \
           seqware/seqware_whitestar_pancancer:1.1.1 \
           bash -c "seqware bundle launch --ini /workflow.ini --dir /workflows/Workflow_Bundle_StoreAndForward_1.0.2_SeqWare_1.1.0/ --engine whitestar --no-metadata"
