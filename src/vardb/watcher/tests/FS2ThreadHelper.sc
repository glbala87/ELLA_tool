import $ivy.`co.fs2::fs2-core:0.10.0-M9`
import $ivy.`co.fs2::fs2-io:0.10.0-M9`

import java.lang.Thread.UncaughtExceptionHandler
import java.util.concurrent.{Executors, ThreadFactory, TimeUnit}
import java.util.concurrent.atomic.AtomicInteger
import java.nio.channels.AsynchronousChannelGroup

import scala.concurrent.ExecutionContext
import scala.util.control.NonFatal

import fs2._

object FS2Helper {

  implicit val ec : ExecutionContext = 
      ExecutionContext.fromExecutor(
        Executors.newFixedThreadPool(
          8, threadFactory("ExecutionContext", daemon = true
      )))

  implicit val scheduler : Scheduler = 
    Scheduler.fromScheduledExecutorService(
      Executors.newScheduledThreadPool(
        4, threadFactory("Scheduler", daemon = true
    )))

  implicit val asynchChannelGroup: AsynchronousChannelGroup = 
    AsynchronousChannelGroup.withThreadPool(
      Executors.newCachedThreadPool(
        threadFactory("AsynchChannelGroup", daemon = true
    )))


  
  def threadFactory(name: String, daemon: Boolean, exitJvmOnFatalError: Boolean = true): ThreadFactory = {
    new ThreadFactory {
      val idx = new AtomicInteger(0)
      val defaultFactory = Executors.defaultThreadFactory()
      def newThread(r: Runnable): Thread = {
        val thread = defaultFactory.newThread(r)
        thread.setName(s"${name}_${idx.incrementAndGet()}")
        thread.setDaemon(daemon)
        thread.setUncaughtExceptionHandler(new UncaughtExceptionHandler {
          def uncaughtException(t: Thread, e: Throwable): Unit = {
            ExecutionContext.defaultReporter(e)
            if (exitJvmOnFatalError) {
              e match {
                case NonFatal(_) => ()
                case fatal => System.exit(-1)
              }
            }
          }
        })
        thread
      }
    }
  }

  def shutdown(): Unit = {
    println("shutting down!")
    asynchChannelGroup.shutdownNow()
    println("awaiting termination ....")
    asynchChannelGroup.awaitTermination(10, TimeUnit.SECONDS)
    println("has shutdown: " + asynchChannelGroup.isShutdown())
    println("has terminated: " + asynchChannelGroup.isTerminated())
  }

}