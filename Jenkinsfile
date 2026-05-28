pipeline {
    agent any

    parameters {
        string(name: 'VERSION', description: 'New version to release (e.g. 1.4.2)', trim: true)
    }

    environment {
        NEXUS_REGISTRY = 'localhost:8082'
        IMAGE          = 'homedashboard-be'
    }

    stages {
        stage('Validate') {
            steps {
                script {
                    if (!params.VERSION?.trim()) {
                        error('VERSION parameter is required')
                    }
                }
            }
        }

        stage('Version') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'forgejo-token',
                                                   usernameVariable: 'GIT_USER',
                                                   passwordVariable: 'GIT_PASS')]) {
                    sh """
                        echo ${params.VERSION} > version
                        git config user.email "jenkins@home"
                        git config user.name "Jenkins"
                        git add version
                        git commit -m "[system] Bump version to ${params.VERSION}"
                        git push http://\$GIT_USER:\$GIT_PASS@git.example.internal/aautrand/homedashboard-be.git HEAD:dev
                    """
                }
            }
        }

        stage('Build') {
            steps {
                sh "podman build -t ${NEXUS_REGISTRY}/${IMAGE}:${params.VERSION} ."
            }
        }

        stage('Push to Nexus') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'nexus-credentials',
                                                   usernameVariable: 'NEXUS_USER',
                                                   passwordVariable: 'NEXUS_PASS')]) {
                    sh """
                        podman login --tls-verify=false ${NEXUS_REGISTRY} -u \$NEXUS_USER -p \$NEXUS_PASS
                        podman push ${NEXUS_REGISTRY}/${IMAGE}:${params.VERSION}
                    """
                }
            }
        }

    }

    post {
        success {
            echo "homedashboard-be ${params.VERSION} pushed to Nexus successfully"
        }
        failure {
            echo "Build/push of ${params.VERSION} failed"
        }
    }
}