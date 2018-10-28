from opv_tasks.task import Task
from opensfm.commands.detect_features import Command as DetectFeatures
from opensfm.commands.match_features import Command as MatchFeatures
from opensfm.commands.create_tracks import Command as CreateTracks
from opensfm.commands.reconstruct import Command as Reconstruct


class OsfmlaunchTask(Task):
    """
        Launch osfm
        Input format :
            opv-task osfmlaunch '{"osfm_dir": OSFM_DIR, "id_malette": ID_MALETTE }'
    """
    TASK_NAME = "osfmlaunch"
    requiredArgsKeys = ["id_malette", "osfm_dir"]

    def runWithExceptions(self, options={}):
        self.checkArgs(options)

        data = type("", (), dict(dataset=options["osfm_dir"]))()

        self.logger.info("Launch detect features")
        command = DetectFeatures()
        command.run(data)
        self.logger.info("Launch match features")
        command = MatchFeatures()
        command.run(data)
        self.logger.info("Launch create tracks")
        command = CreateTracks()
        command.run(data)
        self.logger.info("Launch reconstruct")
        command = Reconstruct()
        command.run(data)
