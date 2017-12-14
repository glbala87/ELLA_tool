#!/usr/bin/env ammonite

/**
* In order to run the script you need to have ammonite installed:
* 
* sudo curl -L -o /usr/local/bin/amm https://git.io/vdNv2 && sudo chmod +x /usr/local/bin/amm && amm
* 
* Or try your default package manager, at least it exists in `brew` 
* 
* Java is probably a prerequisite!
* 
* The script can also be started with :
* amm TestDataGenerator.sc
*
* How it works:
*
* The script is based on Streams created by fs2 scala library. It concatenates the following two Streams:
* 1.)  preparations - database reset and creation
* 2.)  Three parallell streams running in 3 threads, consisting of analysisWatcher, configStream, readyStream 
*
* The three parallel streams will start to run only after the preparations stream has finished. 
* 
* - analysisWatcher runs the python script `analysis_watcher.py` in `/ella/src/vardb/watcher`.
* - configStream creates an analysis folder according to `TestAnalysis-001`.
* - readyStream adds the READY flag inside the folder after the configStream has created the analysis folder.
* 
* IMPORTANT REMARKS: The configStream and readyStream runs with random delays given with the flags CONFIG_DELAY and READY_DELAY
* 
* Ammonite is an amazing tool created by Li Haoyi
*
*/

// library imports
import $ivy.`scalavision::fs2helper:0.1-SNAPSHOT`
import $ivy.`org.json4s::json4s-native:3.5.3`

// json imports
import org.json4s._
import org.json4s.native.Serialization
import org.json4s.native.Serialization.{write}

// fs2 - functional streams imports
import fs2helper.Fs2Helper._
import fs2._
import cats.effect.IO
import scala.concurrent.duration._

// jdbc - functional db imports
import $ivy.`org.tpolecat::doobie-postgres:0.5.0-M10`
import doobie._
import doobie.implicits._

// ammonite shell imports
import ammonite.ops._
// Creating a simple pipe symbol for writing files
import ammonite.ops.{write => wr}
import ammonite.ops.ImplicitWd._

/**
  * Settings and utility functions and values
  */

val CONFIG_DELAY = 30.seconds
val READY_DELAY = 20.seconds
val NR_OF_THREADS = 3

def log[A](prefix: String): Pipe[IO, A, A] = _.evalMap { a =>
  IO{println(s"$prefix> $a"); a }
}

def randomDelays[A](max: FiniteDuration): Pipe[IO, A, A] = _.flatMap { a =>
  val delay = scala.util.Random.nextInt(max.toMillis.toInt)
  println(s"generated delay: $delay ms ")
  scheduler.delay(Stream.eval(IO(a)), delay.millis)
}

// The working directory for the script
val wd = pwd

/**
  * Data Model and Json support
  */

case class Params(genepanel: String)

case class Config(
   params: Params,
   name: String,
   `type`: String,
   priority: Int,
   samples: Array[String] = Array.empty[String]
)

implicit val formats = Serialization.formats(NoTypeHints)
val namePostfix = "TestAnalysis-00"

case class Analysis(
  id: Int, 
  folderName: String, 
  fileName: String, 
  json: String, 
  genepanelName: String, 
  genepanelVersion: String 
)

val jsonConfigs: Stream[IO, Analysis] = Stream(2,3,4,5,6).map { n =>
  val analysisName = s"$namePostfix$n"
  val genepanelName = s"1GP$n"
  val genepanelVersion = s"v$n"
  val config = Config(
      params = Params(s"${genepanelName}_${genepanelVersion}"),
      `type` = "exome",
      name = s"$namePostfix$n",
      priority = n
    )
  Analysis(
    n,
    json = write(config),
    folderName = analysisName, 
    fileName = s"$analysisName.analysis",
    genepanelName = genepanelName,
    genepanelVersion = genepanelVersion
  )
}

/**
  * IO side effects, creating data folders
  */

val analysisFolder = wd/up/'testdata/'analyses

val setReady: Sink[IO, String] = _.evalMap { folderName =>
    IO {
        val path = analysisFolder/folderName
        wr(path/"READY", "")
    }
}

val createTestConfig: Sink[IO, Analysis] = _.evalMap { a =>
  IO {
    val insert =
    s"""insert into genepanel (name, version, genome_reference, config ) values (
          '${a.genepanelName}', '${a.genepanelVersion}', 'GRCh37' , '{}'
    )"""

    val result = %%('docker, 'exec, 'f064a5dfc90d, 'psql, "-U", 'postgres, "-d", 'postgres, "-c", insert)
      
    val path = analysisFolder/a.folderName
    val file = path/a.fileName
    mkdir! path

    // Copying test data from previous vcf sample, sometimes this will fail, but
    // that is intentional, to see that the analyse_watcher.py script can cope with it
    cp(analysisFolder/s"TestAnalysis-00${a.id - 1}"/s"TestAnalysis-00${a.id - 1}.vcf", analysisFolder/a.folderName/s"TestAnalysis-00${a.id}.vcf")

    println("data copied, writing testdata: " + file)
    println(a.json)

    wr(file, a.json)
  }
}

/**
  * Creating and running the streams of IO effects, i.e. test data generation
  */

val readyStream = jsonConfigs.map { c => c.folderName }.through(randomDelays(READY_DELAY)).to(setReady)
val configStream = jsonConfigs.covary[IO].to(createTestConfig)

val preparations = {
  mkdir! wd/up/'testdata/'destination
  %('docker, 'exec, 'f064a5dfc90d, "/ella/ella-cli", 'database, 'drop, "-f")
  %('docker, 'exec, 'f064a5dfc90d, "/ella/ella-cli", 'database, 'make, "-f")
  %('docker, 'exec, 'f064a5dfc90d, 'make, 'dbreset)
}

val analysisWatcher = Stream.eval( IO {
  %('docker, 'exec, 'f064a5dfc90d, 'python, "src/vardb/watcher/analysis_watcher.py", "--analyses", "src/vardb/watcher/testdata/analyses", "--dest", "src/vardb/watcher/testdata/destination")
})

// running configStream and readyStream in parallell on 3 threads.
// ready flag will always be set after the initial test data are created, but 
// ready flag for test data 2 may be set after test data 1.
 val program = Stream(preparations) ++ Stream(analysisWatcher, configStream, readyStream).join(NR_OF_THREADS).through(randomDelays(CONFIG_DELAY)).through(log("data"))
//val program = Stream(configStream, readyStream).join(3).through(randomDelays(4.seconds)).through(log("data"))

println("creating new analysis ..")
program.covary[IO].run.unsafeRunAsync(println)
